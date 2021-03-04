#!/bin/bash

# source all the variables in the docker environment file
# to better simulate a more secure environment
# and also make variables available to test code in python scripts

# get tag from this commit.
# if there's no tag, use 'unstable' to tag the container on commits to master
TX_TAG=`git describe --exact-match --tags $(git log -n1 --pretty='%h')  2> /dev/null; `

function getTAG {
    tag=unstable
    docker build -t $(basename $(pwd)):$tag . 1>&2
    echo $tag
}

set -o allexport
source env.TAG
source test/env.docker
tx_router_tx_persistence_TAG=$(cd tx-persistence && getTAG)
tx_router_TAG=$(getTAG)
set +o allexport

# note that the environmenal variables set above
# will override any .env variables
# setting them explicitly here avoids any ambiguity

### save info on how docker containers were configured
MONGO_INITDB_ROOT_PASSWORD=example MONGO_NON_ROOT_PASSWORD=collection JWT_SECRET=secret docker-compose -f docker-compose.yml -f test/docker-compose.yml config > test/config.out


env > test/env.out

# add other MONGO creds here?
MONGO_INITDB_ROOT_PASSWORD=example MONGO_NON_ROOT_PASSWORD=collection JWT_SECRET=secret docker-compose -f docker-compose.yml -f test/docker-compose.yml up --build -V --exit-code-from txrouter-test
