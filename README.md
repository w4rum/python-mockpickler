# Python MockPickler

Python Pickle variant that wraps unknown classes in a mock class.
These classes can be pickled again and should load correctly on the system in
which the pickle was originally created.

## Usage (Unpickler)
Have a look at the demo with `./demo/run.sh` or re-use the following code
snippet.
```python
import mockpickle as pickle

pickled_data = load_from_somewhere()

mocked_data = pickle.loads(pickled_data)
mocked_data._state["foo"] = "not_foo"
repickled_data = pickle.dumps(mocked_data)
```

## Usage (GUI)
Just run `python3 mockpickler-gui` and try not to choke on the bugs.

Oh, and don't look at the code if you value your eyesight.

## Stability
This is a rather hacky and experimental script.
The repickling relies on ugly eval statements that dynamically load the unknown
modules on the target system.
Because of this, you cannot mockunpickle data that has been dumped with
mockpickler, so `loads(dumps(x))` will fail.
This is because the mockunpickler currently can not handle the `__reduce__`
outputs from `MockObj`.

`list` and `dict` subclasses are treated differently because their contents
are not part of the object attributes (`__dict__`).
Repickling might fail for subclasses of other built-in types.
