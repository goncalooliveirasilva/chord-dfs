"""Tests for consistent hashing utilities."""

import pytest

from src.core.hashing import DEFAULT_M_BITS, dht_hash, is_between


class TestDhtHash:
    """Tests ofr dht_hash function."""

    def test_hash_string(self):
        """Hash a string and get an integer result."""
        result = dht_hash("test")
        assert isinstance(result, int)

    def test_hash_bytes(self):
        """Hash bytes directly."""
        result = dht_hash(b"test")
        assert isinstance(result, int)

    def test_hash_deterministic(self):
        """Same input produces same output."""
        assert dht_hash("hello") == dht_hash("hello")
        assert dht_hash(b"hello") == dht_hash(b"hello")

    def test_hash_string_bytes_equivalent(self):
        """String and its encoded bytes produce same hash."""
        assert dht_hash("hello") == dht_hash(b"hello")

    def test_hash_in_range(self):
        """Hash is within [0, 2^m_bits]."""
        max_value = 2**DEFAULT_M_BITS
        for data in ["test", "node0:5000", "file.txt", ""]:
            result = dht_hash(data)
            assert 0 <= result < max_value

    def test_hash_custom__m_bits(self):
        """Hash respects custom m_bits parameter."""
        result = dht_hash("test", m_bits=8)
        assert 0 <= result <= 256
        result = dht_hash("test", m_bits=16)
        assert 0 <= result <= 65536

    def test_hash_different_inputs(self):
        """Different inputs produce different hashes (with high probability)."""
        # With 10-bit hash (1024 values), use fewer inputs to avoid birthday paradox
        hashes = {dht_hash(f"node{i}") for i in range(100)}
        assert len(hashes) > 90


class TestIsBetween:
    """Tests for is_between circular range check."""

    def test_normal_range(self):
        """Value in normal (non-wraparound) range."""
        assert is_between(10, 20, 15) is True
        assert is_between(10, 20, 10) is False
        assert is_between(10, 20, 20) is True

    def test_outside_normal_range(self):
        """Value ourside normal range."""
        assert is_between(10, 20, 5) is False
        assert is_between(10, 20, 25) is False

    def test_wraparound_range(self):
        """Value in wraparound range (start > end)"""
        # Range (900, 100] on 1024-space wraps around 0
        assert is_between(900, 100, 950) is True  # after start
        assert is_between(900, 100, 50) is True  # before end
        assert is_between(900, 100, 0) is True  # at zero
        assert is_between(900, 100, 100) is True  # at end

    def test_outside_wraparound_range(self):
        """Value outside wraparound range."""
        assert is_between(900, 100, 500) is False
        assert is_between(900, 100, 200) is False
        assert is_between(900, 100, 900) is False

    def test_adjacent_values(self):
        """Edge cases with adjacent values."""
        assert is_between(5, 6, 6) is True
        assert is_between(5, 6, 5) is False

    def test_same_start_end(self):
        """When start equals end, all values are in range (full circle)."""
        # This represents a single-node ring where the node is responsible for all keys
        assert is_between(10, 10, 10) is True
        assert is_between(10, 10, 5) is True
        assert is_between(10, 10, 100) is True

    @pytest.mark.parametrize(
        ("start", "end", "value", "expected"),
        [
            (0, 100, 50, True),
            (0, 100, 0, False),
            (0, 100, 100, True),
            (1000, 50, 1020, True),
            (1000, 50, 30, True),
            (1000, 50, 500, False),
        ],
    )
    def test_parametrized_cases(self, start, end, value, expected):
        """Parametrized test cases for comprehensive coverage."""
        assert is_between(start, end, value) is expected
