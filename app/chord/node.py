'''chor DHT node'''
import time
import logging
import threading
import requests
from app.chord.finger_table import FingerTable
from app.utils.chord_utils import dht_hash, is_between
from app.services import storage_service as STORAGE

TIMEOUT = 10
JOIN_RETRY_INTERVAL = 5
STABILIZE_INTERVAL = 2

logger = logging.getLogger(__name__)

class Node():
    '''HTTP-based node'''
    def __init__(self, address, some_node_address=None):

        self.address = address
        self.id = dht_hash(address)

        self.successor_id = self.id
        self.successor_address = self.address

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

    def get_predecessor(self):
        '''Get predecessor'''
        return {
            "predecessor_id": self.predecessor_id,
            "predecessor_addr": self.predecessor_address
        }


    def handle_join_request(self, joining_id, joining_addr: tuple[str, int]):
        '''Process a join request from another node'''

        logger.debug("[DEBUG][%s] handling join for %s from %s", self.id, joining_id, joining_addr)
        if self.successor_id == self.id:
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
        logger.debug("[%s] Trying to join.", self.id)
        if self.inside_ring or self.some_node_address is None:
            # I'm already in the ring
            logger.debug("[%s] I'm already in the ring", self.id)
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
                self.successor_id = data["successor_id"]
                self.successor_address = tuple(data["successor_addr"])
                self.inside_ring = True
                logger.debug("[%s] Successfully joined DHT", self.id)
            else:
                logger.debug("[DEBUG][%s] join failed with %s", self.id, response.status_code)
        except Exception as e:
            logger.debug("[%s] join request error %s", self.id, e)



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
            self.successor_address = address
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
                logger.debug("[STABILIZE] Notify successor failed: %s", response.status_code)
        except Exception as e:
            logger.debug("[STABILIZE] Exception during notify: %s", e)

        # Refresh finger table entries
        entries_to_refresh = self.finger_table.refresh()
        for (i, lookup_id, address) in entries_to_refresh:

            try:
                # response = requests.post(
                #     f"http://{address[0]}:{address[1]}/chord/successor",
                #     json={
                #         "id": lookup_id,
                #         "requester": self.address
                #     },
                #     timeout=TIMEOUT
                # )
                # if response.ok:
                successor_info = self.find_successor(lookup_id, address)
                successor_id = successor_info["successor_id"]
                successor_addr = tuple(successor_info["successor_addr"])
                self.finger_table.update(i, successor_id, successor_addr)
            except Exception as e:
                logger.debug("[STABILIZE][%s] Error refreshing finger %s: %s", self.id, i, e)


    def put_file(self, filename, file_content):
        '''Store file through DHT'''
        key_hash = dht_hash(filename)
        logger.debug("[DEBUG] File hash: %s", key_hash)
        logger.debug("[%s] Checking if responsible: pred=%s, self=%s, key=%s",
                     self.id, self.predecessor_id, self.id, key_hash)
        if self.predecessor_id is None or is_between(self.predecessor_id, self.id, key_hash):
            # I'm responsible for the file
            STORAGE.save_file(file_content, filename)
            logger.debug("[DEBUG] Stored file %s locally on node %s.", filename, self.id)
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
                logger.debug("[DEBUG] Failed to forward file: %s", e)
                return False


    def get_file(self, filename):
        '''Retrive a file from the DHT'''
        key_hash = dht_hash(filename)
        logger.debug("[DEBUG] Get: %s %s", filename, key_hash)

        if self.predecessor_id is None or is_between(self.predecessor_id, self.id, key_hash):
            # I'm responsible for the file
            file_path = STORAGE.get_file_path(filename)
            if file_path:
                return ("local", file_path)
            return ("not_found", None)
        else:
            next_node_addr = self.finger_table.find(key_hash)
            # I'm not responsible: forward to correct node
            try:
                response = requests.get(
                    f"http://{next_node_addr[0]}:{next_node_addr[1]}/files/{filename}",
                    timeout=TIMEOUT,
                    stream=True
                )
                if response.status_code == 200:
                    return ("forwarded", response.content)
                return ("not_found", None)
            except Exception as e:
                logger.debug("[DEBUG] Failed to forward GET: %s", e)
                return ("error", str(e))


    def delete_file(self, filename):
        '''Delete a file from the DHT'''
        key_hash = dht_hash(filename)
        logger.debug("[DEBUG] Delete: %s %s", filename, key_hash)

        if self.predecessor_id is None or is_between(self.predecessor_id, self.id, key_hash):
            # I'm responsible for the file
            if STORAGE.delete_file(filename):
                return ("deleted", None)
            return ("not_found", None)
        else:
            next_node_addr = self.finger_table.find(key_hash)
            # I'm not responsible: forward to correct node
            try:
                response = requests.delete(
                    f"http://{next_node_addr[0]}:{next_node_addr[1]}/files/{filename}",
                    timeout=TIMEOUT
                )
                if response.status_code == 200:
                    return ("deleted", None)
                return ("not_found", None)
            except Exception as e:
                logger.debug("[DEBUG] Failed to forward DELETE: %s", e)
                return ("error", str(e))


    def list_all_files(self):
        '''List all files stored'''
        return STORAGE.list_files()


    # def delete_all_files(self):
    #     '''Delete all files'''
    #     files = self.list_all_files()
    #     for file in files:
    #         self.delete_file(file)


    def run(self):
        '''Main node loop'''

        threading.Thread(target=self._main_loop, daemon=True).start()


    def _main_loop(self):
        '''Main loop'''

        # Attempt to join the DHT ring
        while not self.inside_ring:
            self.node_join()
            if self.inside_ring:
                # Notify our successor
                self.notify(self.id, self.address)
                self.finger_table.fill(self.successor_id, self.successor_address)
                self.stabilize(None, None) # first stabilize
                logger.debug("[%s] Finished joining, successor is %s", self.id, self.successor_id)
            time.sleep(JOIN_RETRY_INTERVAL)

        # Keep stabilizing
        while True:
            try:
                response = requests.get(
                    f"http://{self.successor_address[0]}:{self.successor_address[1]}/chord/predecessor",
                    timeout=TIMEOUT
                )
                if response.ok:
                    predecessor_info = response.json()
                    from_id = predecessor_info["predecessor_id"]
                    from_addr = predecessor_info["predecessor_addr"]

                    self.stabilize(from_id, from_addr)
            except Exception as e:
                logger.debug("[%s] Stabilize error: %s", self.id, e)
            time.sleep(STABILIZE_INTERVAL)
