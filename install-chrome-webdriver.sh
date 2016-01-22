#!/bin/bash
# This script is used by Travis to install its chromedriver,
# so we can test the application against chrome browser

set -x -e

wget https://chromedriver.storage.googleapis.com/2.20/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/bin
