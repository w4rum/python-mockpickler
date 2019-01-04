# Python MockPickler

Python `pickle` variant that mocks unknown modules and classes.
These classes can be pickled again and should load correctly on the system on
which the pickle was originally created.

## Usage (Unpickler)
Have a look at the demo with `./demo/run.sh` or re-use the following code
snippet.
```python
import mockpickle as pickle

pickled_data = load_from_somewhere()

mocked_data = pickle.loads(pickled_data)
mocked_data.foo = "not_foo"
repickled_data = pickle.dumps(mocked_data)
```

## Usage (GUI)
Just run `python3 mockpickler-gui` and try not to choke on the bugs.

Oh, and don't look at the code if you value your eyesight.

## How it works
Before actually unpickling the data, the `load` functions make a scanning run
in which they dynamically create missing modules and classes.
The rest of the `load` and `dump` functions are the same as in the standard
`pickle` module.

## Limitations
Since pickles only contain module and class names but not any information
regarding superclasses, the scanner tries to guess superclasses based on the
operations that are performed on the mocked classes, e.g. assume `list` as
superclass when `load_appends` is executed on an object of the class.

Currently, only `list` and `dict` subclasses are detected this way.
Subclasses of other built-in types, e.g. `set`, might not unpickle properly.

Since the unpickler does not have any information about an unknown class's
`__getstate__` and `__getnewargs__` functions, the arguments passed to
`__new__` upon unpickling are preserved so that they're not lost when
repickling the data.
This is also done for arguments passed to `__setstate__` if the argument is
not a `dict`.
Otherwise, it's simply copied onto `__dict__`.
