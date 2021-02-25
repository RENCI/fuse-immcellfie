#!/bin/sh
#
# Install script for PDS framework, see: https://github.com/RENCI/pds
#
# PDS is a framework and API specifications aimed at streamlining the
# clinical innovation pipeline from peer-reviewed research to safe,
# effective, validated, evidence-based and personalized clinical
# decision support.
#
# APIs include:
#
#  Guidance - Code to this API if you aim to build a clinical decision
#  support model.
#
#  Mapper - Code to this API if you are a data steward aiming to
#  provide clinically-relevant patient variables extracted from the
#  patient record.
#
#  pds - Code to this API if you wish to build a dashboard or
#  integration for using clinical decision support models
#
#
# MIT License
#
# Copyright (c) 2019 Renaissance Computing Institute
#
#######################################################################
#
#                    System Requirements:
#
#######################################################################
#
# We recommend the following system for deploying the core components:
#
#    OS: Centos 7
#    CPU: 4 Intel ® Xeon ® CPU E5-2698 v3 @ 2.30GHz
#    RAM: 15 G
#    Disk: 50 GB
#
# The following software has been tested for deploying the core
# components:
#
#    Docker v19.03.1
#    Docker-compose v1.24.1
#
# Follow instructions at docker to get the latest version, and to set
# up to run docker as a non-root user
# (https://docs.docker.com/compose/install/).
#
#    git v1.8
#
# Additionally, a service account/unprivileged user will need to be
# provisioned, with access to the installed software.
#
#    A service account (unprivileged user) to run production services
#
#######################################################################
#
#                    Install
#
#######################################################################
#

#######################################################################
#
# Run the full server with a service account (limited privileges) for
# added security, see instructions above for setting up service
# account.
#
# Sometimes docker compose would create a bridge network that
# conflicts with host network. To be sure that the PDS docker bridge
# doesn't collide with host network traffic, as of this release, we
# default the subnet to `172.40.0.0/16`.
#
# If you want set the subnet to a different range because the above
# range collides with your host's traffic, you can change it in
# `test.system/tx-router/test/env.docker`
#
# For more detail:
#   https://stackoverflow.com/questions/50514275/docker-bridge-conflicts-with-host-network
#

echo "####################################################################"
echo "Deploying..."
echo "####################################################################"
./system.sh deploy

echo "####################################################################"
echo "Testing..."
echo "####################################################################"
docker ps
curl -X GET "http://localhost:8080/v1/plugin/pds/config?piid=pdspi-guidance-example" -H "accept: application/json"

echo "Done."

echo "####################################################################"
echo "  NOTE: "
echo "  To remove and restart ALL pds containers:"
echo ""
echo "    source tear-down.src"
echo ""
echo "  then re-run this script to re-deploy"
echo ""
echo ""
echo " Warning: the above commands will REMOVE any and all containers"
echo "installed on the computer, across all users or projects."
echo "####################################################################"

popd