"""Tests for FingerTable class."""

import pytest

from src.core.finger_table import FingerTable
from src.core.hashing import DEFAULT_M_BITS
from src.network.messages import NodeAddress, NodeInfo


@pytest.fixture
def node_address():
    """Create a test node address."""
    return NodeAddress(host="localhost", port=5000)


@pytest.fixture
def finger_table(node_address):
    """Create a finger table for testing."""
    return FingerTable(node_id=100, node_address=node_address)


@pytest.fixture
def other_node():
    """Create another node for testing."""
    return NodeInfo(node_id=200, address=NodeAddress(host="localhost", port=5001))


class TestFingerTableInit:
    """Tests for FingerTable initialization."""

    def test_init_with_defaults(self, node_address):
        """Initialize with default m_bits."""
        ft = FingerTable(node_id=100, node_address=node_address)
        assert ft.node_id == 100
        assert ft.node_address == node_address
        assert ft.m_bits == DEFAULT_M_BITS

    def test_init_custom_m_bits(self, node_address):
        """Initialize with custom m_bits."""
        ft = FingerTable(node_id=100, node_address=node_address, m_bits=8)
        assert ft.m_bits == 8

    def test_init_entries_point_to_self(self, finger_table, node_address):
        """All entries initially point to self."""
        for i in range(1, finger_table.m_bits + 1):
            entry = finger_table.get(i)
            assert entry.node_id == 100
            assert entry.address == node_address


class TestFingerTableOperations:
    """Tests for FingerTable operations."""

    def test_fill(self, finger_table, other_node):
        """Fill all entries with a node."""
        finger_table.fill(other_node)
        for i in range(1, finger_table.m_bits + 1):
            assert finger_table.get(i) == other_node

    def test_update_single_entry(self, finger_table, other_node):
        """Update a single entry."""
        finger_table.update(1, other_node)
        assert finger_table.get(1) == other_node
        # Other entries unchanged
        assert finger_table.get(2).node_id == 100

    def test_update_various_indices(self, finger_table, node_address):
        """Update entries at various indices."""
        for i in range(1, finger_table.m_bits + 1):
            new_node = NodeInfo(node_id=i * 100, address=node_address)
            finger_table.update(i, new_node)
            assert finger_table.get(i).node_id == i * 100

    def test_get_uses_one_based_index(self, finger_table, other_node):
        """Get uses 1-based indexing."""
        finger_table.update(1, other_node)
        assert finger_table.get(1) == other_node


class TestFingerTableSuccessor:
    """Tests for successor property."""

    def test_successor_is_first_entry(self, finger_table, other_node):
        """Successor is the first finger table entry."""
        finger_table.update(1, other_node)
        assert finger_table.successor == other_node

    def test_successor_initially_self(self, finger_table):
        """Successor initially points to self."""
        assert finger_table.successor.node_id == finger_table.node_id


class TestFindClosestPreceding:
    """Tests for find_closest_preceding method."""

    def test_returns_self_when_no_better_option(self, finger_table):
        """Returns first entry when no closer node exists."""
        result = finger_table.find_closest_preceding(500)
        assert result.node_id == finger_table.node_id

    def test_finds_closest_preceding(self, node_address):
        """Finds the closest preceding node from finger table."""
        ft = FingerTable(node_id=0, node_address=node_address)

        # Set up finger table entries
        ft.update(1, NodeInfo(node_id=100, address=node_address))
        ft.update(2, NodeInfo(node_id=200, address=node_address))
        ft.update(3, NodeInfo(node_id=400, address=node_address))

        # Key 350 should return node 200 (closest preceding)
        result = ft.find_closest_preceding(350)
        assert result.node_id == 200

    def test_scans_from_highest_to_lowest(self, node_address):
        """Scans finger table from highest index to lowest."""
        ft = FingerTable(node_id=0, node_address=node_address, m_bits=4)

        # Fill with increasing node IDs
        for i in range(1, 5):
            ft.update(i, NodeInfo(node_id=i * 50, address=node_address))

        # Key 250: should find node 200 (index 4)
        result = ft.find_closest_preceding(250)
        assert result.node_id == 200


class TestGetRefreshTargets:
    """Tests for get_refresh_targets method."""

    def test_returns_correct_number_of_targets(self, finger_table):
        """Returns m_bits number of targets."""
        targets = finger_table.get_refresh_targets()
        assert len(targets) == finger_table.m_bits

    def test_targets_have_correct_structure(self, finger_table):
        """Each target is (index, lookup_key) tuple."""
        targets = finger_table.get_refresh_targets()
        for index, lookup_key in targets:
            assert isinstance(index, int)
            assert isinstance(lookup_key, int)
            assert 1 <= index <= finger_table.m_bits

    def test_lookup_keys_formula(self, node_address):
        """Lookup keys follow (node_id + 2^(i-1)) mod 2^m formula."""
        ft = FingerTable(node_id=100, node_address=node_address, m_bits=4)
        targets = ft.get_refresh_targets()

        expected_keys = [
            (100 + 1) % 16,  # i=1: 100 + 2^0 = 101 % 16 = 5
            (100 + 2) % 16,  # i=2: 100 + 2^1 = 102 % 16 = 6
            (100 + 4) % 16,  # i=3: 100 + 2^2 = 104 % 16 = 8
            (100 + 8) % 16,  # i=4: 100 + 2^3 = 108 % 16 = 12
        ]

        for (_index, key), expected_key in zip(targets, expected_keys, strict=True):
            assert key == expected_key
