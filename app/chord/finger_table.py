'''finger table'''
from app.utils.chord_utils import is_between

class FingerTable:
    '''Finger table'''
    def __init__(self, node_id, node_address, m_bits=10):
        '''Initialize finger table.'''
        self.node_id = node_id
        self.node_address = node_address
        self.m_bits = m_bits
        self.table = []

        for _ in range(0, self.m_bits):
            self.table.append((node_id, node_address))


    def fill(self, node_id, node_address):
        '''Fill all entries of finger table with node_id, node_address.'''

        for i in range(0, self.m_bits):
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

    def get_index_from_id(self, identification):
        '''Get index of finger table entry of id'''

    def __repr__(self):
        return str(self.table)


    def as_list(self):
        '''Return the finger table as a list of tuples: (identifier, (host, port)).
        NOTE: list index 0 corresponds to finger_table index 1
        '''
        return self.table
