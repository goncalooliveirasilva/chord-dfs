'''chord utilities'''
import hashlib

def generate_id(address: tuple[str, int]):
    '''Generates an id based on SHA-1'''
    sha1_hash = hashlib.sha1(str(address).encode("utf-8")).hexdigest()
    return int(sha1_hash, 16)

def is_between(start, end, node):
    '''Check if node is between begin node and end node'''
    if start < end:
        return start < node <= end
    return node > start or node <= end
