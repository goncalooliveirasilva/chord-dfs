'''chor DHT node'''
import requests
from app.chord.finger_table import FingerTable
from app.utils.chord_utils import dht_hash, is_between
from app.services import storage_service as STORAGE

TIMEOUT = 5

class Node():
    '''HTTP-based node'''
    def __init__(self, address, some_node_address=None):

        self.address = address
        self.id = dht_hash(address)

        self.successor_id = None
        self.successor_address = None

        self.predecessor_id = None
        self.predecessor_address = None

        self.some_node_address = some_node_address
        self.inside_ring = False

        self.finger_table = FingerTable(self.id, self.address)

        if self.some_node_address is None:
            # This is the only node into the ring
            self.inside_ring = True
            self.successor_id = self.id
            self.successor_address = self.address


    def handle_join_request(self, joining_id, joining_addr: tuple[str, int]):
        '''Process a join request from another node'''

        print(f"[DEBUG][{self.id}] handling join for {joining_id} from {joining_addr}")
        if self.successor_id == joining_id:
            # There's only one node into the ring, and it's me
            self.successor_id = joining_id
            self.successor_address = joining_addr
            return {
                "successor_id": self.id,
                "successor_addr": self.address
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
                "successor_addr": old_successor_addr
            }
        else:
            # Forward to my successor
            try:
                response = requests.post(
                    f"http://{self.successor_address[0]}:{self.successor_address[1]}/chord/join",
                    json={"id": joining_id, "address": joining_addr},
                    timeout=TIMEOUT
                )
                if response.ok:
                    return response.json()
                return {"error": "Join forward failed"}
            except Exception as e:
                return {"error": f"Exception forwarding join: {str(e)}"}


    def node_join(self):
        '''Initiate join via some node'''
        if self.inside_ring or self.some_node_address is None:
            # I'm already in the ring
            return
        try:
            # I want to join the ring
            response = requests.post(
                f"http://{self.some_node_address[0]}:{self.some_node_address[1]}/chord/join",
                json={"id": self.id, "address": self.address},
                timeout=TIMEOUT
            )
            if response.ok:
                data = response.json()
                self.successor_id = data["id"]
                self.successor_address = tuple(data["address"])
                self.inside_ring = True
            else:
                print(f"[DEBUG][{self.id}] join failed with {response.status_code}")
        except Exception as e:
            print(f"[{self.id}] join request error {e}")



    def find_successor(self, lookup_id, requester_addr):
        '''Get a successor of the node asking'''
        if is_between(self.id, self.successor_id, lookup_id):
            # It's my successor
            return {
                "successor_id": self.successor_id,
                "successor_addr": self.successor_address
            }
        else:
            try:
                response = requests.post(
                    f"http://{self.successor_address[0]}:{self.successor_address[1]}/chord/successor",
                    json={"id": lookup_id, "requester": requester_addr},
                    timeout=TIMEOUT
                )
                if response.ok:
                    return response.json()
                return {"error": "Forwarding find_successor failed"}
            except Exception as e:
                return {"error": str(e)}


    def handle_notify(self, predecessor_id, predecessor_addr):
        '''Process notify call'''
        if self.predecessor_id is None or is_between(
            self.predecessor_id, self.id, predecessor_id
        ):
            self.predecessor_id = predecessor_id
            self.predecessor_address = predecessor_addr
        return {"message": "ACK"}


    def notify(self, predecessor_id, predecessor_addr):
        '''Update predecessors'''
        try:
            response = requests.post(
                f"http://{self.successor_address[0]}:{self.successor_address[1]}/chord/notify",
                json={
                    "predecessor_id": predecessor_id,
                    "predecessor_addr": predecessor_addr,
                },
                timeout=TIMEOUT
            )
            return response.ok
        except Exception as e:
            return {"error": str(e)}


    def stabilize(self, from_id, address):
        '''Update all successors
        from_id: id of the predecessor of node with address address
        address: address of the node sending stabilize  message
        '''
        if from_id is not None and is_between(self.id, self.successor_id, from_id):
            # Update my successor
            self.successor_id = from_id
            self.address = address
            # Update my successor in finger table
            self.finger_table.update(1, from_id, address)

        # Notify my successor, so it can update its predecessor (which is me)
        try:
            response = requests.post(
                f"http://{self.successor_address[0]}:{self.successor_address[1]}/chord/notify",
                json={
                    "predecessor_id": self.id,
                    "predecessor_addr": self.address
                },
                timeout=TIMEOUT
            )
            if not response.ok:
                print(f"[STABILIZE] Notify successor failed: {response.status_code}")
        except Exception as e:
            print(f"[STABILIZE] Exception during notify: {str(e)}")

        # Refresh finger table entries
        entries_to_refresh = self.finger_table.refresh()
        for (i, lookup_id, address) in entries_to_refresh:
            try:
                response = requests.post(
                    f"http://{address[0]}:{address[1]}/chord/successor",
                    json={
                        "id": lookup_id,
                        "requester": self.address
                    },
                    timeout=TIMEOUT
                )
                if response.ok:
                    successor_info = response.json()
                    successor_id = successor_info["successor_id"]
                    successor_addr = tuple(successor_info["successor_addr"].values())
                    self.finger_table.update(i, successor_id, successor_addr)
            except Exception as e:
                print(f"[STABILIZE][{self.id}] Error refreshing finger {i}: {str(e)}")


    def put_file(self, filename, file_content):
        '''Store file through DHT'''
        key_hash = dht_hash(filename)

        if self.predecessor_id is None or is_between(self.predecessor_id, self.id, key_hash):
            # I'm responsible for the file
            STORAGE.save_file(file_content, filename)
            print(f"[DEBUG] Stored file {filename} locally.")
            return True
        else:
            # Forward to the responsible node
            next_node_addr = self.finger_table.find(key_hash)
            try:
                files = {"file": (filename, file_content)}
                response = requests.post(
                    f"http://{next_node_addr[0]}:{next_node_addr[1]}/files/forward",
                    files=files,
                    timeout=TIMEOUT
                )
                return response.ok
            except Exception as e:
                print(f"[DEBUG] Failed to forward file: {str(e)}")
                return False


    def get(self, filename, requester_address):
        '''Retrive a file from the DHT'''
        key_hash = dht_hash(filename)
        print(f"[DEBUG] Get: {filename} {key_hash}")

        if self.predecessor_id is None or is_between(self.predecessor_id, self.id, key_hash):
            # I'm responsible for the file
            pass




    def run(self):
        '''Main loop'''
