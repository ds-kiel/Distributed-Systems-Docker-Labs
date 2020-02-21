#!/bin/bash


if [ "$1" = "" ]
then
  echo "Usage: $0 <number of servers>"
  exit
fi

export NUM_SERVERS=$1
export FROM_PORT=8001
export TO_PORT=$((8000+$NUM_SERVERS))

# We remove existing containers to get consistent numbering
docker-compose rm --force 
docker-compose up --scale server=$NUM_SERVERS



for (( i=2; i <= $max; ++i ))
do
    echo "$i"
done