import re
from fractions import Fraction
from .data import *
from .circularity import *

def lispify(lisp, obj):
    return lispify_datum(decircularize(obj, lisp.readtable))


def lispify_datum(obj):
    return lispifiers[type(obj)](obj)


def lispify_dict(d):
    s = "{"
    for key, value in d.items():
        s += lispify_datum(key) + " " + lispify_datum(value)
    return s + "}"

symbol_regex = re.compile(r"([^:]+:)?:?([^:]+)")


def lispify_str(s):
    def escape(s):
        return s.translate(str.maketrans({'"':'\\"', '\\':'\\\\'}))
    return '"' + escape(s) + '"'


def lispify_UnknownLispObject(x):
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


def lispify_Symbol(x):
    if not x.package:
        return "|" + x.name + "|"
    else:
        return "|" + x.package + "|::|" + x.name + "|"


lispifiers = {
    bool       : lambda x: "T" if x else "NIL",
    type(None) : lambda x: "NIL",
    int        : lambda x: str(x),
    float      : lambda x: str(x),
    complex    : lambda x: "#C(" + lispify_datum(x.real) + " " + lispify_datum(x.imag) + ")",
    list       : lambda x: "#(" + " ".join(lispify_datum(elt) for elt in x) + ")",
    Fraction   : lambda x: str(x),
    str        : lispify_str,
    dict       : lispify_dict,
    Cons       : lispify_Cons,
    Symbol     : lispify_Symbol,
    SharpsignEquals : lambda x: "#" + str(x.label) + "=" + lispify_datum(x.obj),
    SharpsignSharpsign : lambda x: "#" + str(x.label) + "#",
    UnknownLispObject : lispify_UnknownLispObject,
}
