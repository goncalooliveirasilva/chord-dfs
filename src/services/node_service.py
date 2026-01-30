"""Node service for orchestrating Chord DHT operations."""

import asyncio
import contextlib
import logging
from pathlib import Path

from src.core.hashing import dht_hash
from src.core.node import ChordNode
from src.network.http_transport import HttpTransport
from src.network.messages import NodeAddress, NodeInfo
from src.storage.local import LocalStorageBackend

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
        storage_path: str | Path = "/app/storage",
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
            storage_path (str | Path, optional): Path to local storage directory.
                Defaults to "/app/storage".
        """
        self.address = NodeAddress(host=host, port=port)
        self.node_id = dht_hash(f"{host}:{port}", m_bits=m_bits)
        self.m_bits = m_bits
        self.bootstrap_address = bootstrap_address
        self.stabilize_interval = stabilize_interval

        self.node = ChordNode(
            node_id=self.node_id,
            address=self.address,
            m_bits=m_bits,
        )
        self.transport = HttpTransport()
        self.storage = LocalStorageBackend(base_path=storage_path)

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

        await self.storage.initialize()

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
        """Run one iteration of the stabilization protocol.

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

    async def _find_successor_iterative(self, key: int, max_hops: int = 10) -> NodeInfo:
        """Find the successor of a key using iterative finger table lookup.

        Each hop uses the finger table to jump closer to the target,
        guaranteeing O(log N) hops.

        Args:
            key (int): The key to find the successor for
            max_hops (int, optional): Maximum hops to prevent infinite loops. Defaults to 10.

        Returns:
            NodeInfo: The node responsible for the key
        """
        # Start with closest preceding node from our finger table
        current = self.node.finger_table.find_closest_preceding(key)

        # If closest preceding is ourselves, our successor is responsible
        if current.node_id == self.node_id:
            return self.node.successor

        for _ in range(max_hops):
            try:
                # Ask current node for the successor of key
                response = await self.transport.find_successor(
                    target=current.address,
                    key=key,
                    requester_address=self.address,
                )
                result = NodeInfo(
                    node_id=response.successor_id,
                    address=response.successor_address,
                )

                # If the node returns itself, it's the responsible node
                if result.node_id == current.node_id:
                    return result

                current = result
            except Exception as e:
                logger.error("Lookup hop to %s has failed: %s", current.node_id, e)
                return self.node.successor
        return current

    async def handle_join(self, joining_id: int, joining_address: NodeAddress) -> NodeInfo:
        """Handle a join request from another node.

        Uses finger table lookup to find the correct successor for the joining node.

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

        # Use finger table to find the correct successor
        return await self._find_successor_iterative(joining_id)

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

    def get_file_key(self, filename: str) -> int:
        """Get the DHT key for a filename."""
        return dht_hash(filename, m_bits=self.m_bits)

    async def put_file(self, filename: str, content: bytes) -> tuple[bool, str]:
        """Store a file in the distributed file system.

        Routes the file to the responsible node based on filename hash.

        Args:
            filename (str): Name of the file
            content (bytes): File content

        Returns:
            tuple[bool, str]: (success, message/node_id where stored)
        """
        key = self.get_file_key(filename)

        if self.is_responsible_for(key):
            # Store locally
            await self.storage.save(filename, content)
            logger.info("Stored file %s locally (key=%s)", filename, key)
            return True, str(self.node_id)

        # Find the responsible node using iterative lookup
        target = await self._find_successor_iterative(key)
        try:
            success = await self.transport.forward_file(
                target=target.address,
                filename=filename,
                content=content,
            )
            if success:
                logger.info("Forwarded file %s to node %s", filename, target.node_id)
                return True, str(target.node_id)
            return False, "Forward failed"
        except Exception as e:
            logger.error("Failed to forward file %s: %s", filename, e)
            return False, str(e)

    async def get_file(self, filename: str) -> bytes | None:
        """Retrieve a file from the distributed file system.

        Routes the request to the responsible node based on filename hash.

        Args:
            filename (str): Name of the file

        Returns:
            bytes | None: File content if found, None otherwise
        """
        key = self.get_file_key(filename)

        if self.is_responsible_for(key):
            # Get from local storage
            return await self.storage.get(filename)

        # Find the responsible node using iterative lookup
        target = await self._find_successor_iterative(key)
        try:
            return await self.transport.get_file(target=target.address, filename=filename)
        except Exception as e:
            logger.error("Failed to get file %s from node %s: %s", filename, target.node_id, e)
            return None

    async def delete_file(self, filename: str) -> bool:
        """Delete a file from the distributed file system.

        Routes the request to the responsible noode based on filename hash.

        Args:
            filename (str): Name of the file

        Returns:
            bool: True if deleted, False otherwise
        """
        key = self.get_file_key(filename)

        if self.is_responsible_for(key):
            # Delete from local storage
            return await self.storage.delete(filename)

        # Find the responsible node using iterative lookup
        target = await self._find_successor_iterative(key)
        try:
            return await self.transport.delete_file(target=target.address, filename=filename)
        except Exception as e:
            logger.error("Failed to delete file %s from node %s: %s", filename, target.node_id, e)
            return False

    async def list_local_files(self) -> list[str]:
        """List files stored locally on this node.

        Returns:
            list[str]: List of filenames stored locally
        """
        return await self.storage.list_files()

    async def store_file_locally(self, filename: str, content: bytes) -> str:
        """Store a file directly on this node (for forwarded files).

        Args:
            filename (str): Name of the file
            content (bytes): File content

        Returns:
            str: Path where file was stored
        """
        return await self.storage.save(filename, content)
