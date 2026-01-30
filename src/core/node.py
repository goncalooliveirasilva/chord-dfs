"""Chord DHT node logic."""

from dataclasses import dataclass, field

from src.core.finger_table import FingerTable
from src.core.hashing import DEFAULT_M_BITS, is_between
from src.network.messages import NodeAddress, NodeInfo


@dataclass
class ChordNode:
    """Pure Chord node state logic.

    This class implements the core Chord algorithms without any network
    or storage I/O. All methods that would require network calls in the
    paper return routing decisions instead, allowing the caller to
    perform the actual I/O.

    Attributes:
        node_id: This node's identifier in the ring
        address: This node's network address
        m_bits: Number of bits in the identifier space
        predecessor: Current predecessor node, if known
        finger_table: Routing table for O(log N) lookups
    """

    node_id: int
    address: NodeAddress
    m_bits: int = DEFAULT_M_BITS
    predecessor: NodeInfo | None = None
    finger_table: FingerTable = field(init=False)

    def __post_init__(self) -> None:
        """Initialize finger table after dataclass initialization."""
        self.finger_table = FingerTable(
            node_id=self.node_id, node_address=self.address, m_bits=self.m_bits
        )

    @property
    def successor(self) -> NodeInfo:
        """Get the immediate successor (finger[1])."""
        return self.finger_table.successor

    @property
    def info(self) -> NodeInfo:
        """Get this node's identity as NodeInfo."""
        return NodeInfo(node_id=self.node_id, address=self.address)

    def is_alone(self) -> bool:
        """Check if this is the only node in the ring."""
        return self.successor.node_id == self.node_id

    def is_responsible_for(self, key: int) -> bool:
        """Check if this node is responsible for a key.

        A node is responsible for a key k if k is in (predecessor, self].

        Args:
            key (int): The key to check

        Returns:
            bool: True if this node should store/handle the key
        """
        if self.predecessor is None:
            # Only claim responsibility if we're alone in the ring.
            # If we have a successor that isn't us, we're not alone and
            # should defer to lookup until stabilization sets our predecessor.
            return self.is_alone()
        return is_between(self.predecessor.node_id, self.node_id, key)

    def closest_preceding_node(self, key: int) -> NodeInfo:
        """Find the closest preceding node for a key.

        Scans finger table from the highest to lowest looking
        for a finger that precedes the key.

        Args:
            key (int): The key to find preceding node for

        Returns:
            NodeInfo: The closest known node that precedes the key
        """
        return self.finger_table.find_closest_preceding(key)

    def find_successor_local(self, key: int) -> NodeInfo | None:
        """Try to find successor locally without forwarding.

        Returns the successor if key is in (self, successor], otherwise
        return None indicating the request should be forwarded.

        Args:
            key (int): The key to find successor for

        Returns:
            NodeInfo | None: Successor NodeInfo if found locally,
                None if forwarding needed
        """
        if is_between(self.node_id, self.successor.node_id, key):
            return self.successor
        return None

    def get_forward_target(self, key: int) -> NodeInfo:
        """Get the node to forward a lookup request to.

        Args:
            key (int): The key being looked up

        Returns:
            NodeInfo: The best node to forward the request to
        """
        return self.closest_preceding_node(key)

    def should_update_successor(self, successors_predecessor: NodeInfo | None) -> bool:
        """Determine if stabilization should update our successor.

        Called when we learn our successor's predecessor. If that node
        is between us and our current successor, it should become our
        new successor.

        Args:
            successors_predecessor (NodeInfo | None): Our successor's current predecessor

        Returns:
            bool: True if we should adopt successors_predecessor as our new successor
        """
        if successors_predecessor is None:
            return False

        # If we are alone and successor's predecessor is different from us
        if self.is_alone():
            return successors_predecessor.node_id != self.node_id

        return is_between(self.node_id, self.successor.node_id, successors_predecessor.node_id)

    def notify(self, potential_predecessor: NodeInfo) -> bool:
        """Process a notify from a potential predecessor.

        N's thinks it might be our predecessor.
        Update predecessor if n's is between current predecessor and us.

        Args:
            potential_predecessor (NodeInfo): Node claiming to be our predecessor

        Returns:
            bool: True if predecessor was updated
        """
        if self.predecessor is None:
            self.predecessor = potential_predecessor
            return True

        if is_between(self.predecessor.node_id, self.node_id, potential_predecessor.node_id):
            self.predecessor = potential_predecessor
            return True
        return False

    def set_successor(self, successor: NodeInfo) -> None:
        """Update the successor node (finger[1])."""
        self.finger_table.update(1, successor)

    def set_predecessor(self, predecessor: NodeInfo | None) -> None:
        """Update the predecessor node."""
        self.predecessor = predecessor

    def clear_predecessor(self) -> None:
        """Clear predecessor (e.g., when it fails)."""
        self.predecessor = None
