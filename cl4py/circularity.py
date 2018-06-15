import io
from .data import *


class SharpsignSharpsign:
    def __init__(self, label):
        self.label = label


class SharpsignEquals:
    def __init__(self, label, obj):
        self.label = label
        self.obj = obj


def circularize(obj):
    """Modify and return OBJ, such that each instance of SharpsignEquals or
    SharpsignSharpsign is replaced by the corresponding object.
    """
    table = {}
    def copy(obj):
        if isinstance(obj, SharpsignEquals):
            result = copy(obj.obj)
            table[obj.label] = result
            return result
        elif isinstance(obj, Cons):
            return Cons(copy(obj.car),
                        copy(obj.cdr))
        elif isinstance(obj, list):
            return list(copy(elt) for elt in obj)
        else:
            return obj
    def finalize(obj):
        if isinstance(obj, Cons):
            if isinstance(obj.car, SharpsignSharpsign):
                obj.car = table[obj.car.label]
            else:
                finalize(obj.car)
            if isinstance(obj.cdr, SharpsignSharpsign):
                obj.cdr = table[obj.cdr.label]
            else:
                finalize(obj.cdr)
        elif isinstance(obj, list):
            for i in range(len(obj)):
                if isinstance(obj[i], SharpsignSharpsign):
                    obj[i] = table[obj[i].label]
                else:
                    finalize(obj[i])
    result = copy(obj)
    finalize(result)
    return result


def decircularize(obj, readtable):
    """Return a structure that is similar to OBJ, but where each circularity
has been replaced by appropriate SharpsignEquals and SharpsignSharpsign
instances.
    """
    # Utility: Interpret strings as Lisp tokens.
    str_tokens = {}
    def scan_str(s):
        stream = io.StringIO(s)
        token = readtable.read(stream)
        try:
            readtable.read(stream)
            raise RuntimeError('The string "' + s + '" contains more than one token.')
        except EOFError:
            pass
        if not isinstance(token, str):
            str_tokens[s] = token
            scan(token)
    # Phase 1: Scan the data and number all circular objects.
    table = {}
    n = 1
    def scan(obj):
        if isinstance(obj, str):
            scan_str(obj)
            return
        nonlocal n
        atom = not (isinstance(obj, Cons) or
                    isinstance(obj, list) or
                    isinstance(obj, tuple) or
                    isinstance(obj, dict))
        if atom: return
        if obj in table:
            if table[obj] is 0:
                table[obj] = n
                n += 1
            return
        else:
            table[obj] = 0
        if isinstance(obj, Cons):
            scan(obj.car)
            scan(obj.cdr)
        elif isinstance(obj, list):
            for elt in obj:
                scan(elt)
        elif isinstance(obj, tuple):
            for elt in obj:
                scan(elt)
        elif isinstance(obj, dict):
            for key, val in obj.items():
                scan(key)
                scan(val)
    scan(obj)
    # Phase 2: Create a copy of data, where all references have been
    # replaced by SharpsignEquals or SharpsignSharpsign objects.
    def copy(obj):
        # No need to copy atoms.
        if not obj in table:
            return obj
        n = table[obj]
        if n < 0:
            # We have a circular reference.  We use the sign of the
            # object's number to distinguish the first visit from
            # consecutive ones.
            return SharpsignSharpsign(abs(n))
        else:
            if n > 0:
                table[obj] = -table[obj]
            if isinstance(obj, Cons):
                result = Cons(copy(obj.car), copy(obj.cdr))
            elif isinstance(obj, list):
                result = list(copy(elt) for elt in obj)
            elif isinstance(obj, tuple):
                result = List(*(copy(elt) for elt in obj))
            elif isinstance(obj, dict):
                result = {}
                for key, val in obj.items():
                    result[copy(key)] = copy(val)
            elif isinstance(obj, str):
                if obj in str_tokens:
                    return copy(str_tokens[obj])
                else:
                    return obj
            if n > 0:
                return SharpsignEquals(n, result)
            else:
                return result
    return copy(obj)

