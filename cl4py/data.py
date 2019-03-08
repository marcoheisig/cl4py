'''
Correspondence of Python types and Lisp types in cl4py:

| Python                  |     | Lisp                                 |
|-------------------------+-----+--------------------------------------|
| True, False             | <-> | T, NIL                               |
| None                    | --> | NIL                                  |
| int                     | <-> | integer                              |
| float                   | <-> | double-float                         |
| float                   | <-- | single-float                         |
| complex                 | <-> | (complex *)                          |
| string                  | <-> | symbol                               |
| list                    | <-> | simple-vector                        |
| tuple                   | --> | list (+ string to symbol conversion) |
| dict                    | <-> | hash-table                           |
| str                     | <-> | string                               |
| cl4py.Cons              | <-> | cons                                 |
| cl4py.Symbol            | <-> | symbol                               |
| cl4py.UnknownLispObject | <-> | #N? handle                           |
| fractions.Fraction      | <-> | ratio                                |
| numpy.array             | <-> | array                                |

'''
import reprlib

class LispObject:
    pass


class Symbol(LispObject):
    def __init__(self, name, package=None):
        self.name = name
        self.package = package

    def __repr__(self):
        if self.package:
            return 'Symbol("{}", "{}")'.format(self.name, self.package)
        else:
            return 'Symbol("{}", None)'.format(self.name)


class Cons (LispObject):
    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr

    def __len__(self):
        counter = 0
        for x in self:
            counter += 1
        return counter

    @reprlib.recursive_repr("...")
    def __repr__(self):
        datum = self
        car = datum.car
        cdr = datum.cdr
        rcar = repr(car)
        rcdr = repr(cdr)
        if cdr is None:
            return "List(" + rcar + ")"
        elif rcdr.startswith("DottedList("):
            return "DottedList(" + rcar + ", " + rcdr[11:]
        elif rcdr.startswith("List("):
            return "List(" + rcar + ", " + rcdr[5:]
        else:
            return "DottedList(" + rcar + ", " + rcdr + ")"

    def __iter__(self):
        return ListIterator(self)


class UnknownLispObject (LispObject):
    def __init__(self, lisp, handle):
        self.lisp = lisp
        self.handle = handle

    def __del__(self):
        try:
            self.lisp.eval('#{}!'.format(self.handle))
        except:
            pass

    def __call__(self, *args):
        return self.lisp.eval(List(Symbol('FUNCALL', 'CL'), self, *[Quote(arg) for arg in args]))


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


def List(*args):
    head = None
    for arg in args[::-1]:
        head = Cons(arg, head)
    return head


def DottedList(*args):
    head = args[-1] if args else None
    for arg in args[-2::-1]:
        head = Cons(arg, head)
    return head


def Quote(arg):
    return List(Symbol('QUOTE', 'CL'), arg)


def Function(arg):
    return List(Symbol('FUNCTION', 'CL'), arg)


def car(arg):
    if isinstance(arg, Cons):
        return arg.car
    elif not arg:
        return None
    else:
        raise RuntimeError('Cannot take the CAR of ' + str(arg) + '.')


def cdr(arg):
    if isinstance(arg, Cons):
        return arg.cdr
    elif not arg:
        return None
    else:
        raise RuntimeError('Cannot take the CDR of ' + str(arg) + '.')
