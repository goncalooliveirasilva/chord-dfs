## Files

| Action | HTTP | Route | Description |
| ------ | ---- | ----- | ----------- |
| Save a file | POST | /upload/\<filename\> | Upload/store a file |
| Get a file | GET | /files/\<filename\> | Download a file |
| List all files | GET | /files | List all available files |
| Delete a file | DELETE | /files/\<filename\> | Delete a specific file |
| Delete all files | DELETE | /files | Delete all stored files |

## System

| Action | HTTP | Route | Description |
| ------ | ---- | ----- | ----------- |
| Get Successor | GET | /chord/successor | Return successor node's address |
| Keep-alive heartbeat | POST | /chord/keepalive | Node heartbeat (to check if alive) |