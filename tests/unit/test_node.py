"""Tests for ChordNode class."""

import pytest

from src.core.node import ChordNode
from src.network.messages import NodeAddress, NodeInfo


@pytest.fixture
def node_address():
    """Create a test node address."""
    return NodeAddress(host="localhost", port=5000)


@pytest.fixture
def chord_node(node_address):
    """Create a ChordNode for testing."""
    return ChordNode(node_id=100, address=node_address)


@pytest.fixture
def other_node():
    """Create another node for testing."""
    return NodeInfo(node_id=200, address=NodeAddress(host="localhost", port=5001))


class TestChordNodeInit:
    """Tests for ChordNode initialization."""

    def test_init_basic(self, node_address):
        """Initialize a ChordNode."""
        node = ChordNode(node_id=100, address=node_address)
        assert node.node_id == 100
        assert node.address == node_address
        assert node.predecessor is None

    def test_init_creates_finger_table(self, chord_node):
        """Finger table is created on init."""
        assert chord_node.finger_table is not None
        assert chord_node.finger_table.node_id == chord_node.node_id

    def test_info_property(self, chord_node, node_address):
        """Info property returns NodeInfo."""
        info = chord_node.info
        assert info.node_id == 100
        assert info.address == node_address

    def test_successor_initially_self(self, chord_node):
        """Successor initially points to self."""
        assert chord_node.successor.node_id == chord_node.node_id

    def test_is_alone_initially(self, chord_node):
        """Node is alone when successor is self."""
        assert chord_node.is_alone() is True


class TestKeyResponsibility:
    """Tests for is_responsible_for method."""

    def test_responsible_when_no_predecessor(self, chord_node):
        """Responsible for all keys when no predecessor."""
        assert chord_node.is_responsible_for(50) is True
        assert chord_node.is_responsible_for(150) is True
        assert chord_node.is_responsible_for(100) is True

    def test_responsible_for_keys_in_range(self, chord_node):
        """Responsible for keys in (predecessor, self]."""
        chord_node.predecessor = NodeInfo(
            node_id=50, address=NodeAddress(host="localhost", port=5001)
        )
        # Keys in (50, 100]
        assert chord_node.is_responsible_for(75) is True
        assert chord_node.is_responsible_for(100) is True
        assert chord_node.is_responsible_for(50) is False  # exclusive start

    def test_not_responsible_for_keys_outside_range(self, chord_node):
        """Not responsible for keys outside (predecessor, self]."""
        chord_node.predecessor = NodeInfo(
            node_id=50, address=NodeAddress(host="localhost", port=5001)
        )
        assert chord_node.is_responsible_for(25) is False
        assert chord_node.is_responsible_for(150) is False

    def test_responsible_with_wraparound(self, node_address):
        """Handle wraparound case correctly."""
        node = ChordNode(node_id=50, address=node_address)
        node.predecessor = NodeInfo(node_id=900, address=NodeAddress(host="localhost", port=5001))
        # Keys in (900, 50] with wraparound
        assert node.is_responsible_for(950) is True
        assert node.is_responsible_for(0) is True
        assert node.is_responsible_for(50) is True
        assert node.is_responsible_for(500) is False


class TestRouting:
    """Tests for routing methods."""

    def test_closest_preceding_node_delegates(self, chord_node):
        """closest_preceding_node delegates to finger table."""
        result = chord_node.closest_preceding_node(500)
        assert result.node_id == chord_node.node_id

    def test_find_successor_local_found(self, chord_node, other_node):
        """find_successor_local returns successor when key in range."""
        chord_node.set_successor(other_node)
        # Key in (100, 200]
        result = chord_node.find_successor_local(150)
        assert result == other_node

    def test_find_successor_local_not_found(self, chord_node, other_node):
        """find_successor_local returns None when key not in range."""
        chord_node.set_successor(other_node)
        # Key not in (100, 200]
        result = chord_node.find_successor_local(250)
        assert result is None

    def test_get_forward_target(self, chord_node):
        """get_forward_target returns closest preceding node."""
        result = chord_node.get_forward_target(500)
        # Initially returns self (finger table points to self)
        assert result.node_id == chord_node.node_id


class TestStabilization:
    """Tests for stabilization logic."""

    def test_should_update_successor_none_predecessor(self, chord_node):
        """Don't update when successor's predecessor is None."""
        assert chord_node.should_update_successor(None) is False

    def test_should_update_successor_when_alone(self, chord_node):
        """Update successor when alone and predecessor differs."""
        new_node = NodeInfo(node_id=150, address=NodeAddress(host="localhost", port=5001))
        assert chord_node.should_update_successor(new_node) is True

    def test_should_update_successor_when_alone_same_node(self, chord_node):
        """Don't update when alone and predecessor is us."""
        same_node = NodeInfo(node_id=100, address=chord_node.address)
        assert chord_node.should_update_successor(same_node) is False

    def test_should_update_successor_better_node(self, chord_node, other_node):
        """Update when there's a better successor."""
        chord_node.set_successor(other_node)  # successor = 200

        # Node 150 is between us (100) and successor (200)
        better_node = NodeInfo(node_id=150, address=NodeAddress(host="localhost", port=5002))
        assert chord_node.should_update_successor(better_node) is True

    def test_should_not_update_successor_worse_node(self, chord_node, other_node):
        """Don't update when node is not between us and successor."""
        chord_node.set_successor(other_node)  # successor = 200

        # Node 250 is not between us (100) and successor (200)
        worse_node = NodeInfo(node_id=250, address=NodeAddress(host="localhost", port=5002))
        assert chord_node.should_update_successor(worse_node) is False


class TestNotify:
    """Tests for notify method."""

    def test_notify_sets_predecessor_when_none(self, chord_node, other_node):
        """Notify sets predecessor when none exists."""
        result = chord_node.notify(other_node)
        assert result is True
        assert chord_node.predecessor == other_node

    def test_notify_updates_better_predecessor(self, chord_node):
        """Notify updates predecessor when new node is closer."""
        old_pred = NodeInfo(node_id=50, address=NodeAddress(host="localhost", port=5001))
        chord_node.predecessor = old_pred

        # Node 75 is between 50 and 100 (us)
        better_pred = NodeInfo(node_id=75, address=NodeAddress(host="localhost", port=5002))
        result = chord_node.notify(better_pred)
        assert result is True
        assert chord_node.predecessor == better_pred

    def test_notify_ignores_worse_predecessor(self, chord_node):
        """Notify ignores new node that's not closer."""
        old_pred = NodeInfo(node_id=75, address=NodeAddress(host="localhost", port=5001))
        chord_node.predecessor = old_pred

        # Node 50 is not between 75 and 100 (us)
        worse_pred = NodeInfo(node_id=50, address=NodeAddress(host="localhost", port=5002))
        result = chord_node.notify(worse_pred)
        assert result is False
        assert chord_node.predecessor == old_pred


class TestStateUpdates:
    """Tests for state update methods."""

    def test_set_successor(self, chord_node, other_node):
        """set_successor updates finger table entry 1."""
        chord_node.set_successor(other_node)
        assert chord_node.successor == other_node
        assert chord_node.is_alone() is False

    def test_set_predecessor(self, chord_node, other_node):
        """set_predecessor updates predecessor."""
        chord_node.set_predecessor(other_node)
        assert chord_node.predecessor == other_node

    def test_set_predecessor_none(self, chord_node, other_node):
        """set_predecessor can set to None."""
        chord_node.predecessor = other_node
        chord_node.set_predecessor(None)
        assert chord_node.predecessor is None

    def test_clear_predecessor(self, chord_node, other_node):
        """clear_predecessor sets predecessor to None."""
        chord_node.predecessor = other_node
        chord_node.clear_predecessor()
        assert chord_node.predecessor is None
