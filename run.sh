#!/bin/bash
docker run -d -it --env-file .env --name hexdrop-$(date -u +"%Y-%m-%d") hexdrop

docker ps -a