#!/bin/python3

import pickle

filename = "demo-repickled.pickle"

pickled_data = b""
with open(filename, "rb") as f:
    pickled_data = f.read()

demo = pickle.loads(pickled_data)

print("--- After loading on target system:")
print(demo.__dict__)
