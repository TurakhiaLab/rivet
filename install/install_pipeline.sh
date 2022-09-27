#!/bin/bash -ex
#
# Install script for running RIPPLES pipeline on lab server

START_DIR=$PWD

# install dev usher
git clone https://github.com/mrkylesmith/usher.git
cd usher
git checkout recombination_dev

# Run ubuntu build for usher
./install/installUbuntu.sh

cd $START_DIR
