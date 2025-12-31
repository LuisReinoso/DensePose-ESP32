#!/bin/bash
set -e
idf.py set-target esp32s3
idf.py build
idf.py -p ${1:-/dev/ttyUSB0} flash monitor
