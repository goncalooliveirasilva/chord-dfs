'''chor DHT node'''
import requests
from app.utils.chord_utils import generate_id, is_between

TIMEOUT = 5

class Node():
    '''HTTP-based node'''
    def __init__(self, address, some_node_address=None):

        self.address = address
        self.id = generate_id(address)

        self.successor_id = None
        self.successor_address = None

        self.predecessor_id = None
        self.predecessor_address = None

        self.some_node_address = some_node_address
        self.inside_ring = False

        if self.some_node_address is None:
            # This is the only node into the ring
            self.inside_ring = True
            self.successor_id = self.id
            self.successor_address = self.address


    def handle_join_request(self, joining_id, joining_addr: tuple[str, int]):
        '''Process a join request from another node'''

        if self.successor_id == joining_id:
            # There's only one node into the ring
            self.successor_id = joining_id
            self.successor_address = joining_addr
            return {
                "successor_id": self.id,
                "successor_addr": (self.address[0], self.address[1])
            }
        elif is_between(self.id, self.successor_id, joining_id):
            # We are the predecessor of the node trying to join
            # The node trying to join will be our successor

            old_successor_id = self.successor_id
            old_successor_addr = self.successor_address

            self.successor_id = joining_id
            self.successor_address = joining_addr

            return {
                "successor_id": old_successor_id,
                "successor_addr": (old_successor_addr[0], old_successor_addr[1])
            }
        else:
            # Forward to my successor
            try:
                response = requests.post(
                    f"http://{self.successor_address[0]}:{self.successor_address[1]}/chor/join",
                    json={"id": joining_id, "address": joining_addr},
                    timeout=TIMEOUT
                )
                if response.ok:
                    return response.json
                return {"error": "Join forward failed"}
            except Exception as e:
                return {"error": f"Exception forwarding join: {str(e)}"}


    def node_join(self):
        '''Initiate join via some node'''
        if self.inside_ring or self.some_node_address is None:
            # I'm already in the ring
            return
        try:
            response = requests.post(
                f"http://{self.some_node_address[0]}:{self.some_node_address[1]}/chord/join",
                json={"id": self.id, "address": self.address},
                timeout=TIMEOUT
            )
            if response.ok:
                data = response.json()
                self.successor_id = data["id"]
                self.successor_address = tuple(data["address"].values())
                self.inside_ring = True
            else:
                print(f"[{self.id}] join failed with {response.status_code}")
        except Exception as e:
            print(f"[{self.id}] join request error {e}")



    def get_successor(self):
        '''Get a successor of the node asking'''

    def notify(self):
        '''Update predecessors'''

    def stabilize(self):
        '''Update all successors'''

    def put(self, key, value, address):
        '''Store value'''

    def get(self, key, address):
        '''Get a value'''

    def run(self):
        '''Main loop'''
