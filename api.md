## Files

| Action | HTTP | Route | Description | Request | Success response | Error response |
| ------ | ---- | ----- | ----------- | ------- | ---------------- | -------------- |
| Save a file | POST | /files/\<filename\> | Upload/store a file | Field: file to upload | {"message": "File uploaded successfully."} | {"error": "No file provided."} |
| Get a file | GET | /files/\<filename\> | Download a file | (*no body*) | File content (binary download) | {"error": "File not found."} |
| List all files | GET | /files | List all available files | (*no body*) | {"files": ["file1.txt", "file2.txt", ...]} | (*no body*)
| Delete a file | DELETE | /files/\<filename\> | Delete a specific file | (*no body*) | {"message": "File deleted successfully."} | {"error": "File not found."} | 
| Delete all files | DELETE | /files | Delete all stored files | (*no body*) | {"message": "All files deleted"} | (*no body*) |

## System

| Action | HTTP | Route | Description |
| ------ | ---- | ----- | ----------- |
| Get Successor | GET | /chord/successor | Return successor node's address |
| Keep-alive heartbeat | POST | /chord/keepalive | Node heartbeat (to check if alive) |