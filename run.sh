#!/bin/bash

# You must have docker installed

# build the Docker image
docker build -t chord-dfs-image .

# start Docker compose services
docker compose up --build

# To stop: press Ctrl+C
# Then to clean up, run: 'docker compose down'
