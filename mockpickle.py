from pickle import *
from pickle import _Unpickler, _Pickler, _Unframer,\
                   _Stop, bytes_types, _compat_pickle
import io
import pickle
import sys


class _MockUnpickler(_Unpickler):
    """Unpickler variant that wraps unknown classes in a mock class"""

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

    def load_newobj(self):
        args = self.stack.pop()
        cls = self.stack.pop()
        obj = MockObj(cls, args)
        self.append(obj)

    def find_class(self, module, name):
        # Subclasses may override this.
        if self.proto < 3 and self.fix_imports:
            if (module, name) in _compat_pickle.NAME_MAPPING:
                module, name = _compat_pickle.NAME_MAPPING[(module, name)]
            elif module in _compat_pickle.IMPORT_MAPPING:
                module = _compat_pickle.IMPORT_MAPPING[module]
        try:
            __import__(module, level=0)
        except ModuleNotFoundError as e:
            # Just return the full name when the module can't be found
            return "%s.%s" % (module, name)
        if self.proto >= 4:
            return _getattribute(sys.modules[module], name)[0]
        else:
            return getattr(sys.modules[module], name)

    def load_reduce(self):
        stack = self.stack
        args = stack.pop()
        func = stack[-1]
        # Skip reduce calls when the function can't be found
        if type(func) == str:
            self._skippedreduces.append({
                "func": func,
                "args": args
            })
            stack[-1] = None
            return
        stack[-1] = func(*args)

    # Have to redefine dispatcher because the class attribute isn't inherited
    dispatch = {}
    dispatch[PROTO[0]] = _Unpickler.load_proto
    dispatch[FRAME[0]] = _Unpickler.load_frame
    dispatch[PERSID[0]] = _Unpickler.load_persid
    dispatch[BINPERSID[0]] = _Unpickler.load_binpersid
    dispatch[NONE[0]] = _Unpickler.load_none
    dispatch[NEWFALSE[0]] = _Unpickler.load_false
    dispatch[NEWTRUE[0]] = _Unpickler.load_true
    dispatch[INT[0]] = _Unpickler.load_int
    dispatch[BININT[0]] = _Unpickler.load_binint
    dispatch[BININT1[0]] = _Unpickler.load_binint1
    dispatch[BININT2[0]] = _Unpickler.load_binint2
    dispatch[LONG[0]] = _Unpickler.load_long
    dispatch[LONG1[0]] = _Unpickler.load_long1
    dispatch[LONG4[0]] = _Unpickler.load_long4
    dispatch[FLOAT[0]] = _Unpickler.load_float
    dispatch[BINFLOAT[0]] = _Unpickler.load_binfloat
    dispatch[STRING[0]] = _Unpickler.load_string
    dispatch[BINSTRING[0]] = _Unpickler.load_binstring
    dispatch[BINBYTES[0]] = _Unpickler.load_binbytes
    dispatch[UNICODE[0]] = _Unpickler.load_unicode
    dispatch[BINUNICODE[0]] = _Unpickler.load_binunicode
    dispatch[BINUNICODE8[0]] = _Unpickler.load_binunicode8
    dispatch[BINBYTES8[0]] = _Unpickler.load_binbytes8
    dispatch[SHORT_BINSTRING[0]] = _Unpickler.load_short_binstring
    dispatch[SHORT_BINBYTES[0]] = _Unpickler.load_short_binbytes
    dispatch[SHORT_BINUNICODE[0]] = _Unpickler.load_short_binunicode
    dispatch[TUPLE[0]] = _Unpickler.load_tuple
    dispatch[EMPTY_TUPLE[0]] = _Unpickler.load_empty_tuple
    dispatch[TUPLE1[0]] = _Unpickler.load_tuple1
    dispatch[TUPLE2[0]] = _Unpickler.load_tuple2
    dispatch[TUPLE3[0]] = _Unpickler.load_tuple3
    dispatch[EMPTY_LIST[0]] = _Unpickler.load_empty_list
    dispatch[EMPTY_DICT[0]] = _Unpickler.load_empty_dictionary
    dispatch[EMPTY_SET[0]] = _Unpickler.load_empty_set
    dispatch[FROZENSET[0]] = _Unpickler.load_frozenset
    dispatch[LIST[0]] = _Unpickler.load_list
    dispatch[DICT[0]] = _Unpickler.load_dict
    dispatch[INST[0]] = _Unpickler.load_inst
    dispatch[OBJ[0]] = _Unpickler.load_obj
    dispatch[NEWOBJ[0]] = _Unpickler.load_newobj
    dispatch[NEWOBJ_EX[0]] = _Unpickler.load_newobj_ex
    dispatch[GLOBAL[0]] = _Unpickler.load_global
    dispatch[STACK_GLOBAL[0]] = _Unpickler.load_stack_global
    dispatch[EXT1[0]] = _Unpickler.load_ext1
    dispatch[EXT2[0]] = _Unpickler.load_ext2
    dispatch[EXT4[0]] = _Unpickler.load_ext4
    dispatch[POP[0]] = _Unpickler.load_pop
    dispatch[POP_MARK[0]] = _Unpickler.load_pop_mark
    dispatch[DUP[0]] = _Unpickler.load_dup
    dispatch[GET[0]] = _Unpickler.load_get
    dispatch[BINGET[0]] = _Unpickler.load_binget
    dispatch[LONG_BINGET[0]] = _Unpickler.load_long_binget
    dispatch[PUT[0]] = _Unpickler.load_put
    dispatch[BINPUT[0]] = _Unpickler.load_binput
    dispatch[LONG_BINPUT[0]] = _Unpickler.load_long_binput
    dispatch[MEMOIZE[0]] = _Unpickler.load_memoize
    dispatch[APPEND[0]] = _Unpickler.load_append
    dispatch[APPENDS[0]] = _Unpickler.load_appends
    dispatch[SETITEM[0]] = _Unpickler.load_setitem
    dispatch[SETITEMS[0]] = _Unpickler.load_setitems
    dispatch[ADDITEMS[0]] = _Unpickler.load_additems
    dispatch[BUILD[0]] = _Unpickler.load_build
    dispatch[MARK[0]] = _Unpickler.load_mark
    dispatch[STOP[0]] = _Unpickler.load_stop

    # Replace overloaded methods in dispatcher
    dispatch[REDUCE[0]] = load_reduce
    dispatch[NEWOBJ[0]] = load_newobj


# Shorthands

def _load(file, *, fix_imports=True, encoding="ASCII", errors="strict"):
    return _MockUnpickler(file, fix_imports=fix_imports,
                          encoding=encoding, errors=errors).load()


def _loads(s, *, fix_imports=True, encoding="ASCII", errors="strict"):
    if isinstance(s, str):
        raise TypeError("Can't load pickle from unicode string")
    file = io.BytesIO(s)
    return _MockUnpickler(file, fix_imports=fix_imports,
                          encoding=encoding, errors=errors).load()


class MockObj():
    """Catch-all class that is used when an object of an unknown module is to
    be unpickled.
    This class will save the original object's module name, class name, and
    attributes.

    If the original object was a list or dict, then the list and dict contents
    will also be saved.
    """
    def __init__(self, cls, args):
        self._cls = cls         # module and class name
        self._args = args       # constructor arguments
        self._state = {}        # attributes (__dict__ of original object)
        self._picklelist = []   # list contents
        self._pickledict = {}   # dict contents

    def append(self, obj):
        self._picklelist.append(obj)

    def __setitem__(self, key, value):
        self._pickledict[key] = value

    def __setstate__(self, state):
        self._state = state

    def __str__(self):
        if len(self._picklelist) > 0:  # is list
            return str(self._picklelist)
        elif len(self._pickledict) > 0:  # is dict
            return str(self._pickledict)
        else:  # is another type of object
            return str(self._state)

    def __repr__(self):
        if len(self._picklelist) > 0:  # is list
            return repr(self._picklelist)
        elif len(self._pickledict) > 0:  # is dict
            return repr(self._pickledict)
        else:  # is another type of object
            return repr(self._state)

    def __reduce__(self):
        module = self._cls.rpartition('.')[0]
        name = self._cls.rpartition('.')[2]
        # The first two parameters of the return value need to be
        # (func, args), with func(args) returning a new instance
        # of the target class (without calling __init__).
        # To achieve this, we dynamically import the target class's
        # module and then call __new__ like this:
        # module.class.__new__(module.class, *args)
        #
        # Since mocked modules are not present here, we can't
        # evaluate the module and class name here and have to
        # include an indirection via 'eval'
        constructor = ("__import__('%s', fromlist=['%s']).%s.__new__(__import__('%s', fromlist=['%s']).%s,*%s)"\
                       % (module, name, name, module, name, name, self._args),)
        if len(self._picklelist) > 0:  # is list
            return (eval, constructor,
                    self._state, iter(self._picklelist), None)
        elif len(self._pickledict) > 0:  # is dict
            return (eval, constructor,
                    self._state, None, iter(self._pickledict.items()))
        else:  # is another type of object
            return (eval, constructor,
                    self._state, None, None)


# Use the original Pickler, replace the Unpickler
Pickler, Unpickler = _Pickler, _MockUnpickler
dump, dumps, load, loads = pickle.dump, pickle.dumps, _load, _loads
