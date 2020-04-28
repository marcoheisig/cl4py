import re
import numpy
import tempfile
import random
from fractions import Fraction
from .data import *
from .circularity import *

def lispify(lisp, obj):
    return lispify_datum(decircularize(obj, lisp.readtable))


def lispify_datum(obj):
    lispifier = lispifiers.get(type(obj))
    if lispifier:
        return lispifier(obj)
    elif isinstance(obj, LispWrapper):
        return "#{}?".format(obj.handle)
    else:
        raise RuntimeError("Cannot lispify {}.".format(obj))


def lispify_ndarray(A):
    if not A.dtype.hasobject:
        return lispify_specialized_ndarray(A)

    def rec(A):
        if not getattr(A, 'ndim'):
            return lispify_datum(A)
        if A.ndim == 0:
            return " " + lispify_datum(A.item())
        else:
            return "(" + " ".join(rec(a) for a in A) + ")"
    return "#{}A".format(A.ndim) + rec(A)


def lispify_specialized_ndarray(A):
    r = random.randrange(2**63-1)
    tmp = tempfile.gettempdir() + '/cl4py-array-{}.npy'.format(r)
    numpy.save(tmp, A)
    return '#N"{}"'.format(tmp)


def lispify_dict(d):
    s = "{"
    for key, value in d.items():
        s += lispify_datum(key) + " " + lispify_datum(value) + " "
    return s + "}"


def lispify_str(s):
    def escape(s):
        return s.translate(str.maketrans({'"':'\\"', '\\':'\\\\'}))
    return '"' + escape(s) + '"'


def lispify_tuple(x):
    if len(x) == 0:
        return "NIL"
    else:
        # This should never happen, because decircularize implicitly
        # converts tuples to cl4py Lists.
        raise RuntimeError('Cannot lispify non-empty tuple.')


def lispify_Cons(x):
    datum = x
    content = ""
    while isinstance(datum, Cons):
        content += lispify_datum(datum.car) + " "
        datum = datum.cdr
    if not null(datum):
        content += " . " + lispify_datum(datum)
    return "(" + content + ")"


def lispify_Symbol(x):
    if not x.package:
        return "|" + x.name + "|"
    else:
        return "|" + x.package + "|::|" + x.name + "|"


def lispify_Complex(x):
    return "#C(" + lispify_datum(x.real) + " " + lispify_datum(x.imag) + ")"


def lispify_float16(x):
    return '{:E}'.format(x).replace('E', 'S')


def lispify_float32(x):
    return '{:E}'.format(x)


def lispify_float64(x):
    return '{:E}'.format(x).replace('E', 'D')


def lispify_longdouble(x):
    return '{:E}'.format(x).replace('E', 'L')


lispifiers = {
    # Built-in objects.
    bool          : lambda x: "T" if x else "NIL",
    type(None)    : lambda x: "NIL",
    int           : str,
    float         : lispify_float64,
    complex       : lispify_Complex,
    list          : lambda x: "#(" + " ".join(lispify_datum(elt) for elt in x) + ")",
    Fraction      : str,
    tuple         : lispify_tuple,
    str           : lispify_str,
    dict          : lispify_dict,
    # cl4py objects.
    Cons          : lispify_Cons,
    Symbol        : lispify_Symbol,
    Keyword       : lispify_Symbol,
    SharpsignEquals : lambda x: "#" + str(x.label) + "=" + lispify_datum(x.obj),
    SharpsignSharpsign : lambda x: "#" + str(x.label) + "#",
    # Numpy objects.
    numpy.ndarray : lispify_ndarray,
    numpy.str_    : lispify_str,
    numpy.int8    : str,
    numpy.int16   : str,
    numpy.int32   : str,
    numpy.int64   : str,
    numpy.uint8   : str,
    numpy.uint16  : str,
    numpy.uint32  : str,
    numpy.uint64  : str,
    numpy.float16 : lispify_float16,
    numpy.float32 : lispify_float32,
    numpy.float64 : lispify_float64,
    numpy.longdouble : lispify_longdouble,
    numpy.complex64 : lispify_Complex,
    numpy.complex128 : lispify_Complex,
}
