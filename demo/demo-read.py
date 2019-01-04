#!/bin/python3

import sys
sys.path.append('../')
import mockpickle as pickle

filenameIn = "demo.pickle"
filenameOut = "demo-repickled.pickle"

pickled_data = b""
with open(filenameIn, "rb") as f:
    pickled_data = f.read()

mocked_data = pickle.loads(pickled_data)

print("--- Mocked unpickle:")
print(mocked_data.__dict__)

print("--- Manipulating foo in mock object and repickling...")
mocked_data.foo = "not_foo"
print(mocked_data.__dict__)
repickled_data = pickle.dumps(mocked_data)

with open(filenameOut, "wb") as f:
    f.write(repickled_data)
