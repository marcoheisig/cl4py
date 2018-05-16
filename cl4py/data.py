'''
Correspondence of Python types and Lisp types in cl4py:

| Python             |     | Lisp               |
|--------------------+-----+--------------------|
| True, False        | <-> | T, NIL             |
| None               | --> | NIL                |
| int                | <-> | integer            |
| float              | <-> | double-float       |
| float              | <-- | single-float       |
| complex            | <-> | (complex *)        |
| string             | <-> | inserted literally |
| list               | <-> | simple-vector      |
| tuple              | --> | simple-vector      |
| dict               | <-> | hash-table         |
| cl4py.Cons         | <-> | cons               |
| cl4py.String       | <-> | string             |
| cl4py.LispObject   | <-> | #N? handle         |
| fractions.Fraction | <-> | ratio              |
| numpy.array        | <-> | array              |

'''
import re
from fractions import Fraction

class LispObject:
    def __init__(self, lisp, handle):
        self.lisp = lisp
        self.handle = handle

    def __del__(self):
        try:
            self.lisp.eval('#{}!'.format(self.handle))
        except:
            pass

    def __call__(self, *args):
        return self.lisp.eval(List('CL:FUNCALL', self, *args))


class ListIterator:
    def __init__(self, elt):
        self.elt = elt

    def __iter__(self):
        return self

    def __next__(self):
        if isinstance(self.elt, Cons):
            value = self.elt.car
            self.elt = self.elt.cdr
            return value
        else:
            raise StopIteration

class Cons:
   def __init__(self, car, cdr):
       self.car = car
       self.cdr = cdr

   def __repr__(self):
       datum = self
       content = ""
       # TODO handle circularity
       while isinstance(datum, Cons):
           content += repr(datum.car)
           datum = datum.cdr
           if isinstance(datum, Cons):
               content += ", "
       if datum != None:
           return "cl4py.Cons(" + repr(self.car) + ", " + repr(self.cdr) + ")"
       return "cl4py.List(" + content + ")"

   def __iter__(self):
       return ListIterator(self)

class String:
    def __init__(self, data):
        if not isinstance(data, str):
            raise RuntimeError("Not a string: " + str(data))
        self.data = data

    def __repr__(self):
        return "cl4py.String(" + repr(self.data) + ")"

    def __str__(self):
        return str(self.data)


def List(*args):
    head = None
    for arg in args[::-1]:
        head = Cons(arg, head)
    return head


def ListQ(*args):
    return List('CL:QUOTE', List(*args))


def sexp(obj):
    if obj is True:
        return "T"
    elif obj is False or obj is None:
        return "NIL"
    elif isinstance(obj,int):
        return str(obj)
    elif isinstance(obj,float):
        return str(obj)
    #TODO complex
    elif isinstance(obj,str):
        return obj
    elif isinstance(obj, list) or isinstance(obj, tuple):
        return "#(" + " ".join(sexp(elt) for elt in obj) + ")"
    # TODO dict
    elif isinstance(obj,Cons):
       datum = obj
       content = ""
       # TODO handle circularity
       while isinstance(datum, Cons):
           content += sexp(datum.car) + " "
           datum = datum.cdr
       if datum != None:
           content += " . " + sexp(datum)
       return "(" + content + ")"
    elif isinstance(obj, String):
        def escape(s):
            return s.translate(str.maketrans({'"':'\\"', '\\':'\\\\'}))
        return '"' + escape(obj.data) + '"'
    elif isinstance(obj, LispObject):
        return "#{}?".format(obj.handle)
    elif isinstance(obj, Fraction):
        return str(obj)
    else:
        raise RuntimeError('Cannot represent ' + str(token) + ' as an s-expression.')


exponent_markers = 'DdEdFfLlSs'
integer_regex = re.compile(r"[+-]?[0-9]+\.?")
ratio_regex = re.compile(r"([+-]?[0-9]+)/([0-9]+)")
float_regex = re.compile(r"[+-]?[0-9]*\.[0-9]+")
symbol_regex = re.compile(r"([^:]+:)?:?([^:]+)")


def parse(token):
    # integer
    m = re.fullmatch(integer_regex, token)
    if m:
        return int(m.group(0))
    # ratio
    m = re.fullmatch(ratio_regex, token)
    if m:
        return Fraction(int(m.group(1)), int(m.group(2)))
    # float
    m = re.fullmatch(float_regex, token)
    if m:
        # TODO handle all exponent markers
        return float(token)
    # symbol
    m = re.fullmatch(symbol_regex, token)
    if m:
        pkg = m.group(1)
        name = m.group(2)
        if pkg in ['CL', 'COMMON-LISP', None]:
            if name == 'T': return True
            if name == 'NIL': return False
        return token
    raise RuntimeError('Failed to parse token "' + token + '".')
