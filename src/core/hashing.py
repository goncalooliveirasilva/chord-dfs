"""Consistent hashing utilities for Chord DHT."""

import hashlib

DEFAULT_M_BITS = 10


def dht_hash(data: str | bytes, m_bits: int = DEFAULT_M_BITS) -> int:
    """Generate a hash ID using SHA-1

    Args:
        data (str | bytes): Data to hash
        m_bits (int, optional): Number of bits in the identifier space. Defaults to DEFAULT_M_BITS.

    Returns:
        int: Hash value in range [0, 2^m_bits]
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    sha1_hash = hashlib.sha1(data).hexdigest()
    return int(sha1_hash, 16) % (2**m_bits)


def is_between(start: int, end: int, value: int) -> bool:
    """Check if value is in the circular range (start, end].

    Handles wraparound in the circular identifier space.

    Args:
        start (int): Start of range (exclusive)
        end (int): End of range (inclusive)
        value (int): Value to check

    Returns:
        bool: True if value is in (start, end]
    """
    if start < end:
        return start < value <= end
    # Wraparound case
    return value > start or value <= end
