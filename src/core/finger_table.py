"""Finger table for O(log N) lookups in Chord DHT."""

from dataclasses import dataclass, field

from src.core.hashing import DEFAULT_M_BITS, is_between
from src.network.messages import NodeAddress, NodeInfo


@dataclass
class FingerTable:
    """Routing table for efficient key lookup.

    Each entry i points to the first node that succeeds
    (node_id + 2^(i-1)) mod 2^m in the identifier space.
    """

    node_id: int
    node_address: NodeAddress
    m_bits: int = DEFAULT_M_BITS
    _entries: list[NodeInfo] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        """Initialize finger table with self as all entries."""
        self_info = NodeInfo(node_id=self.node_id, address=self.node_address)
        self._entries = [self_info for _ in range(self.m_bits)]

    def fill(self, node: NodeInfo) -> None:
        """Fill all entries with the given node.

        Args:
            node (NodeInfo): Node to fill all entries with
        """
        self._entries = [node for _ in range(self.m_bits)]

    def update(self, index: int, node: NodeInfo) -> None:
        """Update a specific finger table entry

        Args:
            index (int): 1-based index of the entry to update
            node (NodeInfo): Node information to store
        """
        self._entries[index - 1] = node

    def get(self, index: int) -> NodeInfo:
        """Get a specific finger table entry.

        Args:
            index (int): 1-based index of the entry

        Returns:
            NodeInfo: Node at the specified index
        """
        return self._entries[index - 1]

    def find_closest_preceding(self, key: int) -> NodeInfo:
        """Find the closest preceding node for a key.

        Args:
            key (int): Key to find closest preceding node for

        Returns:
            NodeInfo: Closest preceding node from the finger table
        """
        for i in range(self.m_bits - 1, -1, -1):
            entry = self._entries[i]
            if is_between(self.node_id, key - 1, entry.node_id):
                return entry
        return self._entries[0]

    def get_refresh_targets(self) -> list[tuple[int, int]]:
        """Get the keys that need to be lookep up to refresh the finger table.

        Returns:
            list[tuple[int, int]]: List of (index, lookup_key) pairs
        """
        targets = []
        for i in range(1, self.m_bits + 1):
            lookup_key = (self.node_id + (2 ** (i - 1))) % (2**self.m_bits)
            targets.append((i, lookup_key))
        return targets

    @property
    def successor(self) -> NodeInfo:
        """Get the immediate successor (first finger).

        Returns:
            NodeInfo: The successor node
        """
        return self._entries[0]

    def get_node_ids(self) -> list[int]:
        """Get the node IDs from all finger table entries.

        Returns:
            list[int]: List of node IDs in the finger table
        """
        return [entry.node_id for entry in self._entries]
