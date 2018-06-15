from fractions import Fraction
from .data import *
from .circularity import *

def lispify(lisp, obj):
    return lispify_aux(decircularize(obj, lisp.readtable))


def lispify_aux(obj):
    return lispifiers[type(obj)](obj)


def lispify_LispObject(x):
    return "#{}?".format(x.handle)


def lispify_Cons(x):
    datum = x
    content = ""
    while isinstance(datum, Cons):
        content += lispify_aux(datum.car) + " "
        datum = datum.cdr
    if datum != None:
        content += " . " + lispify_aux(datum)
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
    complex    : lambda x: "#C(" + lispify_aux(x.real) + " " + lispify_aux(x.imag) + ")",
    list       : lambda x: "#(" + " ".join(lispify_aux(elt) for elt in x) + ")",
    tuple      : lambda x: lispify_aux(List(*x)),
    # dict     : lambda x: TODO
    Fraction   : lambda x: str(x),
    str        : lambda x: x,
    LispObject : lispify_LispObject,
    Cons       : lispify_Cons,
    String     : lispify_String,
    SharpsignEquals : lambda x: "#" + str(x.label) + "=" + lispify_aux(x.obj),
    SharpsignSharpsign : lambda x: "#" + str(x.label) + "#",
}
