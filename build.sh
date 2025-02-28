#!/bin/bash

# Default: do not use no-cache
NO_CACHE=false
DOCKER_IMAGE_NAME="hexdrop"

usage() {
  echo "Usage: $0 [-c] [-h]"
  echo "   -c  Use no-cache for docker build"
  echo "   -h  Display this help message"
  exit 0
}

# Parse options
while getopts "ch" opt; do
  case ${opt} in
    c )
      NO_CACHE=true
      ;;
    h )
      usage
      ;;
    \? )
      usage
      ;;
  esac
done

# Run the appropriate docker build command
if [ "$NO_CACHE" = true ]; then
  echo "Running: docker build --no-cache -t $DOCKER_IMAGE_NAME ."
  docker build --no-cache -t $DOCKER_IMAGE_NAME .
else
  echo "Running: docker build -t $DOCKER_IMAGE_NAME."
  docker build -t $DOCKER_IMAGE_NAME .
fi
