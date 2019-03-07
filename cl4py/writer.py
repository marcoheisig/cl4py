import re
from fractions import Fraction
from .data import *
from .circularity import *

def lispify(lisp, obj):
    return lispify_datum(decircularize(obj, lisp.readtable))


def lispify_datum(obj):
    return lispifiers[type(obj)](obj)


def lispify_dict(d):
    raise RuntimeError('Not yet implemented, sorry.')

symbol_regex = re.compile(r"([^:]+:)?:?([^:]+)")


def lispify_str(s):
    m = re.fullmatch(symbol_regex, s)
    if m:
        return s
    else:
        raise RuntimeError('Not a symbol: ' + s + '.')


def lispify_LispObject(x):
    return "#{}?".format(x.handle)


def lispify_Cons(x):
    datum = x
    content = ""
    while isinstance(datum, Cons):
        content += lispify_datum(datum.car) + " "
        datum = datum.cdr
    if datum != None:
        content += " . " + lispify_datum(datum)
    return "(" + content + ")"


def lispify_String(x):
    def escape(s):
        return s.translate(str.maketrans({'"':'\\"', '\\':'\\\\'}))
    return '"' + escape(str(x)) + '"'


lispifiers = {
    bool       : lambda x: "T" if x else "NIL",
    type(None) : lambda x: "NIL",
    int        : lambda x: str(x),
    float      : lambda x: str(x),
    complex    : lambda x: "#C(" + lispify_datum(x.real) + " " + lispify_datum(x.imag) + ")",
    list       : lambda x: "#(" + " ".join(lispify_datum(elt) for elt in x) + ")",
    tuple      : lambda x: "#(" + " ".join(lispify_datum(elt) for elt in x) + ")",
    Fraction   : lambda x: str(x),
    str        : lispify_str,
    dict       : lispify_dict,
    LispObject : lispify_LispObject,
    Cons       : lispify_Cons,
    String     : lispify_String,
    SharpsignEquals : lambda x: "#" + str(x.label) + "=" + lispify_datum(x.obj),
    SharpsignSharpsign : lambda x: "#" + str(x.label) + "#",
}
