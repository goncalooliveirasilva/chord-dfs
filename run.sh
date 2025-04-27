#!/bin/bash
docker build -t chord-dfs-image .
docker compose up --build
# To stop run: docker compose down
