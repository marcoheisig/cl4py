import io
from fractions import Fraction
from .data import *
from .circularity import *

def lispify(lisp, obj):
    return lispify_aux(lisp, decircularize(obj))


def lispify_aux(lisp, obj):
    return lispifiers[type(obj)](lisp, obj)


def lispify_str(l, x):
    stream = io.StringIO(x)
    value = l.readtable.read(stream)
    try:
        l.readtable.read(stream)
        raise RuntimeError('The string "' + x + '" contains more than one token.')
    except EOFError:
        pass
    if isinstance(value, str):
        return value
    else:
        return lispify_aux(l, value)


def lispify_LispObject(l, x):
    return "#{}?".format(x.handle)


def lispify_Cons(l, x):
    datum = x
    content = ""
    while isinstance(datum, Cons):
        content += lispify_aux(l, datum.car) + " "
        datum = datum.cdr
    if datum != None:
        content += " . " + lispify_aux(l, datum)
    return "(" + content + ")"


def lispify_String(l, x):
    def escape(s):
        return s.translate(str.maketrans({'"':'\\"', '\\':'\\\\'}))
    return '"' + escape(str(x)) + '"'


lispifiers = {
    bool       : lambda l, x: "T" if x else "NIL",
    type(None) : lambda l, x: "NIL",
    int        : lambda l, x: str(x),
    float      : lambda l, x: str(x),
    complex    : lambda l, x: "#C(" + lispify_aux(l, x.real) + " " + lispify_aux(l, x.imag) + ")",
    list       : lambda l, x: "#(" + " ".join(lispify_aux(l, elt) for elt in x) + ")",
    tuple      : lambda l, x: lispify_aux(l, List(*x)),
    # dict     : lambda x: TODO
    Fraction   : lambda l, x: str(x),
    str        : lispify_str,
    LispObject : lispify_LispObject,
    Cons       : lispify_Cons,
    String     : lispify_String,
    SharpsignEquals : lambda l, x: "#" + str(x.label) + "=" + lispify_aux(l, x.obj),
    SharpsignSharpsign : lambda l, x: "#" + str(x.label) + "#",
}
