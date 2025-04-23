'''chor DHT node'''
from app.utils.chord_utils import generate_id

class Node():
    '''A node from the ring'''
    def __init__(self, address):
        self.address = address
        self.id = generate_id(address)
        self.successor_id = None
        self.predecessor_id = None

    def set_successor_id(self, successor_id):
        '''Set successor id'''
        self.successor_id = successor_id

    def set_predecessor(self, predecessor_id):
        '''Set predecessor id'''
        self.predecessor_id = predecessor_id
