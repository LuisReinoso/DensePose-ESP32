#!/bin/bash
set -e
idf.py set-target esp32s3
idf.py build
echo "idf.py flash monitor"
