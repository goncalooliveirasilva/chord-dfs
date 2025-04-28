# chord-dfs
**chord-dfs** is a decentralized distributed file system (DFS) based on the **Chord Distributed Hash Table (DHT)** protocol. Files are **hashed** and **stored** across multiple nodes connected in a **Chord ring**. The goal is to create a simple **fault-tolerant** and **scalable** DFS system. I'm using Python, Flask and Docker.

## What It Can Do Now?
- Join and organize nodes into a Chord ring using consistent hashing
- Upload and store files across multiple nodes
- Each node runs inside a Docker container


## How To Run

To setup the system you must have Docker installed and running on your computer. Then, follow the next commands:
```
git clone git@github.com:goncalooliveirasilva/chord-dfs.git
cd chord-dfs
./run.sh
```
The (```run.sh```) script will build the Docker image and start Docker compose services.
For now, the Chord ring has only just 5 nodes (seted up on [docker-compose.yml](docker-compose.yml)), but you can add more if you want.
To upload, download or delete files, you only need to use the [Files API](docs/files_api.md).
Now, the best way is through (```curl```) but in the future an web UI will be added (see Future Plans to know more about what's comming!).

**Upload Files**
```
curl -X POST -F "file=@<filename>" http://127.0.0.1:5000/files
```

**Delete  Files**
```
# delete a specific file
curl -X DELETE http://127.0.0.1:5000/files/<filename>

# delete all files
curl -X DELETE http://127.0.0.1:5000/files
```

**Download Files**
```
# only see the content
curl -X GET http://127.0.0.1:5000/files/<filename>

# actually download
curl -O  http://127.0.0.1:5000/files/<filename>
```

In these exemples I use (```port 5000```) which is the node0 (first node) port, but you of course can upload, delete ou download a file from the node you want.
Dont't forget to replace (```<filename>```) with an existing file!
Once you start the Docker containers, the data you store into them will be deleted.
In the future a way to make data persist will be added.

## Documentation

[Files API](docs/files_api.md) - List of endpoints used by the file service.
[System API](docs/system_api.md) - List of endpoints used by the Chord system.


## Future Plans

- Simple web interface: Upload, download and monitor nodes through a web UI
- Dynamic node joins/leaves: Allow nodes to join or leave without compromising file storage
- File chunking: Split files into chunks and distribute them across nodes
- Fault tolerance: Replicate file chunks across other nodes
- User accounts: Allow users to register, log in, and access only their own files.

## References
To develop this project I based myself on [this chord implementation](https://github.com/detiuaveiro/cd_chord) and on [this paper](https://pdos.csail.mit.edu/papers/ton:chord/paper-ton.pdf).