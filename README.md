# chord-dfs
**chord-dfs** is a decentralized distributed file system (DFS) built on the **Chord Distributed Hash Table (DHT)** protocol. Files are **hashed** and **distributed** across multiple nodes connected in a **Chord ring**. The goal is to provide a simple, **fault-tolerant**, and **scalable** DFS system.
This project is implemented using **Python**, **Flask**, and **Docker**.

## Features

- Organize nodes into a Chord ring using consistent hashing
- Upload and store files across distributed nodes
- Run each node in an isolated Docker container


## How To Run

### Requirements
- Docker installed and running

### Clone and Start
```bash
git clone git@github.com:goncalooliveirasilva/chord-dfs.git
cd chord-dfs
./run.sh
```
The ```run.sh``` script builds the Docker image and starts the system with 5 nodes by default. To run more nodes, you'll need to update the 
[docker-compose.yml](docker-compose.yml) or modify the script.

#### Using the API
The DFS exposes a REST API for interaction.
You can use ```curl``` to upload, download, and delete files. A UI is planned for the future (see Future Plans to learn more about what's coming up!).

**Upload a File**
```
curl -X POST -F "file=@<filename>" http://127.0.0.1:5000/files
```

**Delete a File**
```
# delete a specific file
curl -X DELETE http://127.0.0.1:5000/files/<filename>

# delete all files (not fully implemented yet)
curl -X DELETE http://127.0.0.1:5000/files
```

**Download a File**
```
# only see the content
curl -X GET http://127.0.0.1:5000/files/<filename>

# actually download
curl -O http://127.0.0.1:5000/files/<filename>
```

**List Files**
```
# get all file names stored (not fully implemented yet)
curl -X GET http://127.0.0.1:5000/files
```

These examples use port ```5000``` which corresponds to node0. Other nodes are accessible via ports ```5001``` to ```5004```.
You can upload, download or delete files from any node.
Dont't forget to replace ```<filename>``` with the name of an existing file!

## Limitations
- **Data persistence**: Stored files are lost when Docker containers are stopped. A persistence mechanism is planned.
- ```DELETE all files``` and ```list files``` are not fully implemented yet.

## Documentation

[Files API](docs/files_api.md) - Endpoints for file upload/download/delete.  

[System API](docs/system_api.md) - Endpoints related to Chord ring operations.


## Future Plans

Some ideas to make this project more robust and user-friendly:

- **Data persistence**: Use Docker volumes to retain files across container restarts
- **Simple web interface**: Upload, download and monitor nodes via a UI
- **Dynamic node joins/leaves**: Add and remove nodes without affecting the system
- **File chunking**: Split large files across nodes
- **Fault tolerance**: Replicate data for reliability
- **User accounts**: Support for authentication and user-specific storage

## References
To develop this project I based myself on [this chord implementation](https://github.com/detiuaveiro/cd_chord) and on [this paper](https://pdos.csail.mit.edu/papers/ton:chord/paper-ton.pdf).