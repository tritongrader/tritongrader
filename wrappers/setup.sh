#!/bin/sh -e
apt update
apt upgrade -y
# TODO add any extra dependencies of your autograder here
apt install -y python3-zstd build-essential
# TODO perform any other setup, if necessary
