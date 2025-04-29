## System API

| Action | HTTP | Route | Description | Request | Success response | Error response |
| ------ | ---- | ----- | ----------- | ------- | ---------------- | -------------- |
| Forward a file to next node | POST | /files/forward | Forward a file to next node | {"file": (filename, file_content)} | {"message": "File stored successfully."} | {"error": "Failed to store file"} |
| Find Successor | POST | /chord/successor | Return successor node's address | {"id": lookup_id, "requester": requester_addr} | {"successor_id": successor_id, "successor_addr": successor_address} | {"error": "Forwarding find_successor failed"} |
| Get Predecessor | GET | /chord/predecessor | Return predecessor node's address | (*no body*) | {"predecessor_id": predecessor_id, "predecessor_addr": predecessor_address} | (*no body*) |
| Join the ring | POST | /chord/join | Node trying to join the ring | {"address" : address, "id": id} (of the node trying to join) | {"successor_id": successor_id, "successor_addr": successor_addr} | {"error": "Join forward failed"} |
| Update predecessor pointers | POST | /chord/notify | Update predecessor pointers | {"predecessor_id": id, "predecessor_addr": address} | {"message": "ACK"} | (*no body*) |
| Keep-alive heartbeat | POST | /chord/keepalive | Node heartbeat (to check if alive) | (*not yet implemented*) | (*not yet implemented*) | (*not yet implemented*) |
| Get info from a node | GET | /chord/info | Information about a node | (*no body*) | {"id": id, "address": address, "successor_id": successor_id, "successor_addr": successor_addr, "predecessor_id": predecessor_id, "predecessor_addr": predecessor_addr, "finger_table": finger_table, "files": files} | (*no body*) |