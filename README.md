# fuse-immcellfie

Main API, tickets, and project board to be used by dashboards supporting ImmCellFIE project

modeled after pds-release, but this will also include code/submodule for a dashboard

## Running

`docker-compose up`

## Building

`docker build -t fuse-immcellfie-cellfie .`

## Linting

For linting this project using the python linter "black"

## Running test

`docker build -f test/Dockerfile -t test_fuse .`

`docker run test_fuse`
