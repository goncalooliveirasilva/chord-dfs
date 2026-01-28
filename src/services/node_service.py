"""Node service for orchestrating Chord DHT operations."""

import asyncio
import contextlib
import logging

from src.core.hashing import dht_hash
from src.core.node import ChordNode
from src.network.http_transport import HttpTransport
from src.network.messages import NodeAddress, NodeInfo

logger = logging.getLogger(__name__)

DEFAULT_STABILIZE_INTERVAL = 2.0
DEFAULT_JOIN_RETRY_INTERVAL = 5.0


class NodeService:
    """Service that orchestrates Chord node operations.

    Manages the ChordNode state, handles network communications via Transport,
    and runs the stabilization loop as an asyncio task.
    """

    def __init__(
        self,
        host: str,
        port: int,
        bootstrap_address: tuple[str, int] | None = None,
        m_bits: int = 10,
        stabilize_interval: float = DEFAULT_STABILIZE_INTERVAL,
    ) -> None:
        """Initialize the node service.

        Args:
            host (str): Node's hostname
            port (int): Node's port
            bootstrap_address (tuple[str, int] | None, optional): Address of a node
                to join through, or None if first node. Defaults to None.
            m_bits (int, optional): Number of bits in identifier space.
                Defaults to 10.
            stabilize_interval (float, optional): Seconds between stabilization
                runs. Defaults to DEFAULT_STABILIZE_INTERVAL.
        """
        self.address = NodeAddress(host=host, port=port)
        self.node_id = dht_hash(f"{host}:{port}", m_bits=m_bits)
        self.bootstrap_address = bootstrap_address
        self.stabilize_interval = stabilize_interval

        self.node = ChordNode(
            node_id=self.node_id,
            address=self.address,
            m_bits=m_bits,
        )
        self.transport = HttpTransport()

        self._stabilize_task: asyncio.Task[None] | None = None
        self._running = False

    @property
    def info(self) -> NodeInfo:
        """Get this node's info."""
        return self.node.info

    async def start(self) -> None:
        """Start the node service.

        Joins the ring if bootstrap address is provided, then starts
        the stabilization loop.
        """
        logger.info("Starting node %s at %s", self.node_id, self.address)

        if self.bootstrap_address:
            await self._join_ring()

        self._running = True
        self._stabilize_task = asyncio.create_task(self._stabilization_loop())
        logger.info("Node %s started, stabilization loop running", self.node_id)

    async def stop(self) -> None:
        """Stop the node service."""
        logger.info("Stopping node %s", self.node_id)
        self._running = False

        if self._stabilize_task:
            self._stabilize_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._stabilize_task

        await self.transport.close()
        logger.info("Node %s stopped", self.node_id)

    async def _join_ring(self) -> None:
        """Join the Chord ring through the bootstrap node."""
        if not self.bootstrap_address:
            return

        bootstrap = NodeAddress(
            host=self.bootstrap_address[0],
            port=self.bootstrap_address[1],
        )

        while True:
            try:
                logger.info("Attempting to join ring via %s", bootstrap)
                response = await self.transport.join(
                    target=bootstrap,
                    node_id=self.node_id,
                    node_address=self.address,
                )
                successor = NodeInfo(
                    node_id=response.successor_id, address=response.successor_address
                )
                self.node.set_successor(successor)
                self.node.finger_table.fill(successor)

                logger.info("Joined ring, successor is %s", successor.node_id)

                # Notify successor about us
                await self.transport.notify(
                    target=successor.address,
                    predecessor_id=self.node_id,
                    predecessor_address=self.address,
                )
                return
            except Exception as e:
                logger.warning("Join attempt failed: %s, retrying...", e)
                await asyncio.sleep(DEFAULT_JOIN_RETRY_INTERVAL)

    async def _stabilization_loop(self) -> None:
        """Run the stabilization protocol periodically."""
        while self._running:
            try:
                await self._stabilize()
            except Exception as e:
                logger.warning("Stabilization error: %s", e)
            await asyncio.sleep(self.stabilize_interval)

    async def _stabilize(self) -> None:
        """run one iteration of the stabilization protocol.

        1. Get successor's predecessor
        2. If that node is between us and successor, adopt it as new successor
        3. Notify successor about us
        4. Refresh finger table entries
        """
        successor = self.node.successor

        # Skip if we are alone
        if self.node.is_alone():
            return

        try:
            pred_response = await self.transport.get_predecessor(successor.address)

            if pred_response.predecessor_id is not None:
                potential_successor = NodeInfo(
                    node_id=pred_response.predecessor_id,
                    address=pred_response.predecessor_address,
                )

                # Check if we should update our successor
                if self.node.should_update_successor(potential_successor):
                    self.node.set_successor(potential_successor)
                    logger.debug("Updated successor to %s", potential_successor.node_id)

            # Notify successor about us
            await self.transport.notify(
                target=self.node.successor.address,
                predecessor_id=self.node_id,
                predecessor_address=self.address,
            )

            # Refresh finger table
            await self._refresh_fingers()

        except Exception as e:
            logger.debug("Stabilize iteration failed: %s", e)

    async def _refresh_fingers(self) -> None:
        """Refresh finger table entries."""
        targets = self.node.finger_table.get_refresh_targets()

        for index, lookup_key in targets:
            try:
                response = await self.transport.find_successor(
                    target=self.node.successor.address,
                    key=lookup_key,
                    requester_address=self.address,
                )
                successor = NodeInfo(
                    node_id=response.successor_id,
                    address=response.successor_address,
                )
                self.node.finger_table.update(index, successor)
            except Exception as e:
                logger.debug("Failed to refresh finger %s: %s", index, e)

    def handle_join(self, joining_id: int, joining_address: NodeAddress) -> NodeInfo:
        """Handle a join request from another node.

        Args:
            joining_id (int): ID of the joining node
            joining_address (NodeAddress): Address of the joining node

        Returns:
            NodeInfo: Successor info for the joining node
        """
        joining_node = NodeInfo(node_id=joining_id, address=joining_address)

        # If we are alone, the joining node becomes our successor
        if self.node.is_alone():
            self.node.set_successor(joining_node)
            return self.node.info

        # Check if joining node falls between us and our successor
        local_result = self.node.find_successor_local(joining_id)
        if local_result:
            # Joining node should have our current successor as its successor
            old_successor = self.node.successor
            self.node.set_successor(joining_node)
            return old_successor

        # Otherwise return our successor (forwarding will be handled by caller)
        return self.node.successor

    def handle_notify(self, predecessor_id: int, predecessor_address: NodeAddress) -> bool:
        """Handle a notify request from a potential predecessor.

        Args:
            predecessor_id (int): ID of the potential predecessor
            predecessor_address (NodeAddress): Address of the potential predecessor

        Returns:
            bool: True if predecessor was updated
        """
        potential_pred = NodeInfo(node_id=predecessor_id, address=predecessor_address)
        return self.node.notify(potential_pred)

    def get_predecessor(self) -> NodeInfo | None:
        """Get this node's predecessor."""
        return self.node.predecessor

    def is_responsible_for(self, key: int) -> bool:
        """Check if this node is responsible for a key."""
        return self.node.is_responsible_for(key)

    def get_forward_target(self, key: int) -> NodeInfo:
        """Get the node to forward a request to for a key."""
        return self.node.get_forward_target(key)
