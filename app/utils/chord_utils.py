'''chord utilities'''
import hashlib

def generate_id(address: tuple[str, int]):
    '''Generates an id based on SHA-1'''
    sha1_hash = hashlib.sha1(str(address).encode("utf-8")).hexdigest()
    return int(sha1_hash, 16)
