## Files

| Action | HTTP | Route | Description | Request | Success response | Error response |
| ------ | ---- | ----- | ----------- | ------- | ---------------- | -------------- |
| Save a file | POST | /files | Upload/store a file | Field: file to upload | {"message": "File uploaded successfully."} | {"error": "No file provided."} |
| Get a file | GET | /files/\<filename\> | Download a file | (*no body*) | File content (binary download) | {"error": "File not found."} |
| List all files | GET | /files | List all available files | (*no body*) | {"files": ["file1.txt", "file2.txt", ...]} | (*no body*)
| Delete a file | DELETE | /files/\<filename\> | Delete a specific file | (*no body*) | {"message": "File deleted successfully."} | {"error": "File not found."} | 
| Delete all files | DELETE | /files | Delete all stored files | (*no body*) | {"message": "All files deleted"} | (*no body*) |

## System

| Action | HTTP | Route | Description | Request | Success response | Error response |
| ------ | ---- | ----- | ----------- | ------- | ---------------- | -------------- |
| Find Successor | POST | /chord/successor | Return successor node's address | {"id": lookup_id, "requester": requester_addr} | {"successor_id": successor_id, "successor_addr": successor_address} | 
| Get Predecessor | GET | /chord/predecessor | Return predecessor node's address |
| Join the ring | POST | /chord/join | Node trying to join the ring | {"address" : address, "id": id} (of the node trying to join) |
| Update predecessor pointers | POST | /chord/notify | Update predecessor pointers | {"predecessor_id": id, "predecessor_address": address} | {"message": "ACK"}
| Keep-alive heartbeat | POST | /chord/keepalive | Node heartbeat (to check if alive) |
| Get info from a node | GET | /chord/info | Information about a node | (*no body*) | {"id": id, "address": address, "successor_id": successor_id, "successor_addr": successor_addr, "predecessor_id": predecessor_id, "predecessor_addr": predecessor_addr, "finger_table": finger_table} | (*no body*) |