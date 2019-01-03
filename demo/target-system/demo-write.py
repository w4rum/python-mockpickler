#!/bin/python3

import pickle
from democlass import DemoClass

filename = "demo.pickle"

demo = DemoClass()
print("--- Demo object after __init__:")
print(demo.__dict__)

print("--- After manipulating bar on target system:")
demo.setBar("different_bar")
print(demo.__dict__)

# Write to pickle
pickled_data = pickle.dumps(demo)

with open(filename, "wb") as f:
    f.write(pickled_data)
