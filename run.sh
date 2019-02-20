#!/bin/bash

docker build \
  --tag vtk_server_test \
  .

docker run \
  --rm \
  --interactive \
  --tty \
  --name vtk_demo_server \
  --volume "$PWD:/wd:ro" \
  --publish "5000:5000" \
  $@ \
  vtk_server_test
