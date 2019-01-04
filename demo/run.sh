#!/bin/sh

rm demo.pickle demo-repickled.pickle

python3 target-system/demo-write.py
python3 demo-read.py
python3 target-system/demo-read-target.py
