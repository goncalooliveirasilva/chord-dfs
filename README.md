# chord-dfs
**chord-dfs** is a decentralized distributed file system (DFS) based on the **Chord Distributed Hash Table (DHT)** protocol. Files are **hashed** and **stored** across multiple nodes connected in a **Chord ring**. The goal is to create a simple **fault-tolerant** and **scalable** DFS system.

## What it can do now?
- Join and organize nodes into a Chord ring using consistent hashing
- Upload and store files across multiple nodes
- Each node runs inside a Docker container

## Tech Stack
- Python
- Flask
- Docker

## How to run (Coming soon)
Instructions for setting up nodes, uploading and downloading files will be added soon.

## Future plans

- User accounts: Allow users to register, log in, and access only their own files.
- File chunking: Split files into chunks and distribute them across nodes
- Fault tolerance: Replicate file chunks across other nodes
- Dynamic node joins/leaves: Allow nodes to join or leave without compromising file storage
- Simple web interface: Upload, download and monitor nodes through a web UI

## References
To develop this project I based myself on [this chord implementation](https://github.com/detiuaveiro/cd_chord) and on [this paper](https://pdos.csail.mit.edu/papers/ton:chord/paper-ton.pdf).