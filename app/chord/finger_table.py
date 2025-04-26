'''finger table'''

class FingerTable:
    '''Finger table'''
    def __init__(self, node_id, node_address, m_bits=10):
        '''Initialize finger table.'''
        self.node_id = node_id
        self.node_address = node_address
        self.m_bits = m_bits
        self.table = []

        for _ in range(0, self.m_bits, 1):
            self.table.append((node_id, node_address))


    def fill(self, node_id, node_address):
        '''Fill all entries of finger table with node_id, node_address.'''

    def update(self, index, node_id, node_address):
        '''Update index of table with node_id, node_address.'''

    def find(self, id):
        '''Get node address of closest preceding node (in finger table) of id.'''

    def refresh(self):
        '''Retrieve finger table entries requiring refresh.'''

    def get_index_from_id(self, id):
        '''Get index of finger table entry of id'''

    def __repr__(self):
        return str(self.table)


    def as_list(self):
        '''Return the finger table as a list of tuples: (identifier, (host, port)).
        NOTE: list index 0 corresponds to finger_table index 1
        '''
        return self.table
