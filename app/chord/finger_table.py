'''finger table'''
from math import log2
from app.utils.chord_utils import is_between

class FingerTable:
    '''Finger table'''
    def __init__(self, node_id, node_address, m_bits=10):
        '''Initialize finger table.'''
        self.node_id = node_id
        self.node_address = node_address
        self.m_bits = m_bits
        self.table = []

        for _ in range(self.m_bits):
            self.table.append((node_id, node_address))


    def fill(self, node_id, node_address):
        '''Fill all entries of finger table with node_id, node_address.'''
        for i in range(self.m_bits):
            self.table[i] = (node_id, node_address)


    def update(self, index, node_id, node_address):
        '''Update index of table with node_id, node_address.'''
        self.table[index-1] = (node_id, node_address)


    def find(self, identification):
        '''Get node address of closest preceding node (in finger table) of id.'''
        for i in range(self.m_bits - 1, -1, -1):
            (node_id, node_address) = self.table[i]
            if is_between(self.node_id, identification - 1, node_id):
                return node_address
        return self.table[0][1]


    def refresh(self):
        '''Retrieve finger table entries requiring refresh.'''
        entries = []
        for i in range(1, self.m_bits + 1):
            lookup_id = (self.node_id + (2**(i-1))) % (2**self.m_bits)
            address = self.table[self.get_index_from_id(lookup_id) - 1][1]
            entries.append((i, lookup_id, address))
        return entries


    def get_index_from_id(self, identification):
        '''Get index of finger table entry of id'''
        return int(log2((identification - self.node_id) % (2**self.m_bits))) + 1


    def __repr__(self):
        return str(self.table)
