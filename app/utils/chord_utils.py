'''chord utilities'''
import hashlib

def dht_hash(data, m_bits=10):
    '''Generates an id based on SHA-1'''
    sha1_hash = hashlib.sha1(str(data).encode("utf-8")).hexdigest()
    return int(sha1_hash, 16) % 2**m_bits

def is_between(start, end, node):
    '''Check if node is between begin node and end node'''
    if start < end:
        return start < node <= end
    return node > start or node <= end
