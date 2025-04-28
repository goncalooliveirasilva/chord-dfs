## System API

| Action | HTTP | Route | Description | Request | Success response | Error response |
| ------ | ---- | ----- | ----------- | ------- | ---------------- | -------------- |
| Forward a file to next node | POST | /files/forward | Forward a file to next node | {"file": (filename, file_content)} |
| Find Successor | POST | /chord/successor | Return successor node's address | {"id": lookup_id, "requester": requester_addr} | {"successor_id": successor_id, "successor_addr": successor_address} | 
| Get Predecessor | GET | /chord/predecessor | Return predecessor node's address |
| Join the ring | POST | /chord/join | Node trying to join the ring | {"address" : address, "id": id} (of the node trying to join) |
| Update predecessor pointers | POST | /chord/notify | Update predecessor pointers | {"predecessor_id": id, "predecessor_addr": address} | {"message": "ACK"}
| Keep-alive heartbeat | POST | /chord/keepalive | Node heartbeat (to check if alive) |
| Get info from a node | GET | /chord/info | Information about a node | (*no body*) | {"id": id, "address": address, "successor_id": successor_id, "successor_addr": successor_addr, "predecessor_id": predecessor_id, "predecessor_addr": predecessor_addr, "finger_table": finger_table} | (*no body*) |