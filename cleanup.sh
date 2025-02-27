#!/bin/bash
docker ps -a | grep hexdrop|awk '{print $1}' | xargs sudo docker stop $i
docker ps -a | grep hexdrop|awk '{print $1}' | xargs sudo docker rm $i