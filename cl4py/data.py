'''
Correspondence of Python types and Lisp types in cl4py:

| Python             |     | Lisp                                 |
|--------------------+-----+--------------------------------------|
| True               | <-> | T                                    |
| ()                 | <-> | NIL                                  |
| None               | --> | NIL                                  |
| int                | <-> | integer                              |
| float              | <-> | double-float                         |
| float              | <-- | single-float                         |
| complex            | <-> | (complex *)                          |
| string             | <-> | symbol                               |
| list               | <-> | simple-vector                        |
| tuple              | --> | list (+ string to symbol conversion) |
| dict               | <-> | hash-table                           |
| str                | <-> | string                               |
| cl4py.Cons         | <-> | cons                                 |
| cl4py.Symbol       | <-> | symbol                               |
| cl4py.LispWrapper  | <-> | #N? handle                           |
| fractions.Fraction | <-> | ratio                                |
| numpy.array        | <-> | array                                |

'''
import reprlib

class LispObject:
    pass


class Stream(LispObject):
    def __init__(self, textstream):
        self.stream = textstream
        self.old = None
        self.new = None
    def read_char(self, eof_error=True):
        if self.new == None:
            c = self.stream.read(1)
            if eof_error and not c: raise EOFError()
        else:
            c = self.new
        self.old, self.new = c, None
        return c
    def unread_char(self):
        if self.old:
            self.old, self.new = None, self.old
        else:
            raise RuntimeError('Duplicate unread_char.')


class Symbol(LispObject):
    def __init__(self, name, package=None):
        self.name = name
        self.package = package

    def __repr__(self):
        if self.package:
            return 'Symbol("{}", "{}")'.format(self.name, self.package)
        else:
            return 'Symbol("{}", None)'.format(self.name)


class Keyword(Symbol):
    def __init__(self, name):
        super(Keyword, self).__init__(name, 'KEYWORD')

    def __repr__(self):
        return 'Keyword("{}")'.format(self.name)


class Package(LispObject, type(reprlib)):
    def __getitem__(self, name):
        return self.__dict__[name]


class Cons (LispObject):
    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr

    @reprlib.recursive_repr("...")
    def __repr__(self):
        datum = self
        car = datum.car
        cdr = datum.cdr
        rcar = repr(car)
        rcdr = repr(cdr)
        if null(cdr):
            return "List(" + rcar + ")"
        elif rcdr.startswith("DottedList("):
            return "DottedList(" + rcar + ", " + rcdr[11:]
        elif rcdr.startswith("List("):
            return "List(" + rcar + ", " + rcdr[5:]
        else:
            return "DottedList(" + rcar + ", " + rcdr + ")"

    def __iter__(self):
        return ListIterator(self)


class LispWrapper (LispObject):
    def __init__(self, lisp, handle):
        self.lisp = lisp
        self.handle = handle

    def __del__(self):
        try:
            self.lisp.eval('#{}!'.format(self.handle))
        except:
            pass

    def __call__(self, *args):
        return self.lisp.eval(List(Symbol('FUNCALL', 'CL'), Quote(self), *[Quote(arg) for arg in args]))


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
    head = ()
    for arg in args[::-1]:
        head = Cons(arg, head)
    return head


def DottedList(*args):
    head = args[-1] if args else ()
    for arg in args[-2::-1]:
        head = Cons(arg, head)
    return head


def Quote(arg):
    return List(Symbol('QUOTE', 'CL'), arg)


def car(arg):
    if isinstance(arg, Cons):
        return arg.car
    elif null(arg):
        return ()
    else:
        raise RuntimeError('Cannot take the CAR of ' + str(arg) + '.')


def cdr(arg):
    if isinstance(arg, Cons):
        return arg.cdr
    elif null(arg):
        return ()
    else:
        raise RuntimeError('Cannot take the CDR of ' + str(arg) + '.')


def null(arg):
    if arg is ():
        return True
    if (isinstance(arg,Symbol)
        and arg.name == "NIL"
        and (arg.package == "COMMON-LISP" or
             arg.package == "CL")):
        return True
    else:
        return False
