#!/bin/bash

# You must have docker installed

# build the Docker image
echo "[chord-dfs] Building image"
docker build -t chord-dfs-image .

# start Docker compose services
echo -e "\n\n[chord-dfs] Starting Docker compose services\n\n"
docker compose up --build

# To stop: press Ctrl+C twice
# Then to clean up, run: 'docker compose down'
