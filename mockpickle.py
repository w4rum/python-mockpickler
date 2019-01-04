from pickle import *
from pickle import _Unpickler, _Pickler, _Unframer,\
                   _Stop, bytes_types, _compat_pickle
from copy import copy
import pickle
import io
import sys
import types
import importlib


def recreate_object(obj, cls):
    newobj = cls.__new__(cls)
    newobj.__dict__ = obj.__dict__
    return newobj


def add_superclass(obj, supercls):
    # modify class and re-initialize object
    oldcls = type(obj)
    curcls = getattr(sys.modules[oldcls.__module__], oldcls.__name__)
    # skip if class has already been updated
    if issubclass(curcls, supercls):
        return recreate_object(obj, curcls)

    module = oldcls.__module__
    cls = type(oldcls.__name__, (MockBase, supercls), {})
    cls.__module__ = module
    cls.__customclass__ = True
    setattr(sys.modules[module], cls.__name__, cls)

    return recreate_object(obj, cls)


def getbaseclass(cls):
    bases = cls.__bases__
    if list in bases:
        return list
    elif dict in bases:
        return dict
    return object


class _MockScanner(_Unpickler):
    """Unpickler variant that scans a pickle for unknown modules and classes
    and mocks them so that the standard Pickler und Unpickler can handle
    them.

    This class will merely mock missing classes, not actually unpickle sensible
    objects.
    The return value of this class's load function should be discarded."""

    def load(self):
        """Read a pickled object representation from the open file.

        Return the reconstituted object hierarchy specified in the file.
        """
        # Check whether Unpickler was initialized correctly. This is
        # only needed to mimic the behavior of _pickle.Unpickler.dump().
        if not hasattr(self, "_file_read"):
            raise UnpicklingError("Unpickler.__init__() was not called by "
                                  "%s.__init__()" % (self.__class__.__name__,))
        self._unframer = _Unframer(self._file_read, self._file_readline)
        self.read = self._unframer.read
        self.readline = self._unframer.readline
        self.metastack = []
        self.stack = []
        self.append = self.stack.append
        self.proto = 0
        read = self.read
        dispatch = self.dispatch
        self._skippedreduces = []
        try:
            while True:
                key = read(1)
                if not key:
                    raise EOFError
                assert isinstance(key, bytes_types)
                dispatch[key[0]](self)
        except _Stop as stopinst:
            return stopinst.value

    def create_module(self, name, parent=""):
        curlevel, _, child = name.partition('.')
        curmod = parent + curlevel

        if curmod not in sys.modules:
            newmod = types.ModuleType(curmod)
            sys.modules[newmod.__name__] = newmod

        if child != "":  # go further down
            self.create_module(child, parent=curmod + ".")

    def find_class(self, module, name):
        if self.proto < 3 and self.fix_imports:
            if (module, name) in _compat_pickle.NAME_MAPPING:
                module, name = _compat_pickle.NAME_MAPPING[(module, name)]
            elif module in _compat_pickle.IMPORT_MAPPING:
                module = _compat_pickle.IMPORT_MAPPING[module]
        try:
            __import__(module, level=0)
        except ModuleNotFoundError:
            # Create the new module dynamically
            self.create_module(module)
            __import__(module, level=0)
        try:
            if self.proto >= 4:
                return _getattribute(sys.modules[module], name)[0]
            else:
                return getattr(sys.modules[module], name)
        except AttributeError:
            # Create the class dynamically
            cls = type(name, (MockBase,), {})
            # self.custominstances[cls] = []
            cls.__module__ = module
            cls.__customclass__ = True
            setattr(sys.modules[module], name, cls)
            return cls

    def load_setitem(self):
        stack = self.stack
        value = stack.pop()
        key = stack.pop()
        curdict = stack[-1]
        if not issubclass(type(curdict), dict):
            newobj = add_superclass(curdict, dict)
            self.stack[-1] = newobj

    def load_setitems(self):
        items = self.pop_mark()
        curdict = self.stack[-1]
        if not issubclass(type(curdict), dict):
            newobj = add_superclass(curdict, dict)
            self.stack[-1] = newobj

    def load_build(self):
        stack = self.stack
        state = stack.pop()
        inst = stack[-1]
        setstate = getattr(inst, "__setstate__", None)
        if setstate is not None:
            setstate(state)
            return
        slotstate = None
        if isinstance(state, tuple) and len(state) == 2:
            state, slotstate = state
        if state:
            inst_dict = inst.__dict__
            intern = sys.intern
            for k, v in state.items():
                if type(k) is str:
                    inst_dict[intern(k)] = v
                else:
                    inst_dict[k] = v
        if slotstate:
            for k, v in slotstate.items():
                setattr(inst, k, v)

    def load_append(self):
        stack = self.stack
        value = stack.pop()
        curlist = stack[-1]
        if not issubclass(type(curlist), list):
            newobj = add_superclass(curlist, list)
            self.stack[-1] = newobj

    def load_appends(self):
        items = self.pop_mark()
        list_obj = self.stack[-1]
        if not issubclass(type(list_obj), list):
            newobj = add_superclass(list_obj, list)
            self.stack[-1] = newobj

    # Have to redefine dispatcher because the class attribute isn't inherited
    dispatch = copy(_Unpickler.dispatch)

    # Replace overloaded methods in dispatcher
    dispatch[SETITEMS[0]] = load_setitems
    dispatch[BUILD[0]] = load_build
    dispatch[SETITEM[0]] = load_setitem
    dispatch[APPEND[0]] = load_append
    dispatch[APPENDS[0]] = load_appends


def _load(file, *, fix_imports=True, encoding="ASCII", errors="strict"):
    # Scan for unknown classes
    _MockScanner(file, fix_imports=fix_imports,
                 encoding=encoding, errors=errors).load()
    file.seek(0)
    x = pickle._Unpickler(file, fix_imports=fix_imports,
                          encoding=encoding, errors=errors).load()
    return x


def _loads(s, *, fix_imports=True, encoding="ASCII", errors="strict"):
    if isinstance(s, str):
        raise TypeError("Can't load pickle from unicode string")
    file = io.BytesIO(s)
    return _load(file, fix_imports=fix_imports,
                 encoding=encoding, errors=errors)


class MockBase:

    def __new__(cls, *args):
        baseclass = getbaseclass(cls)
        self = baseclass.__new__(cls)
        self._newargs = args
        return self

    def __getnewargs__(self):
        """May only be called once."""
        newargs = self._newargs
        del self._newargs
        return newargs

    def __setstate__(self, state):
        newargs = self._newargs
        if isinstance(state, tuple):
            # just pick the first tuple that is a dictionary
            for x in state:
                if isinstance(x, dict):
                    self.__dict__ = x
                    self._specialstate = state
                    break
        elif isinstance(state, dict):
            self.__dict__ = state
        else:  # fallback for classes with custom __getstate__
            self._specialstate = state
        self._newargs = newargs

    def __getstate__(self):
        """May only be called once."""
        if "_specialstate" in self.__dict__:
            specialstate = self._specialstate
            del self._specialstate
            return specialstate
        else:
            return self.__dict__


# Use the original Pickler, replace the load functions
Pickler, Unpickler = _Pickler, _Unpickler
dump, dumps, load, loads = pickle.dump, pickle.dumps, _load, _loads
