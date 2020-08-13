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
    def __init__(self, textstream, debug=False):
        self.stream = textstream
        self.old = None
        self.new = None
        self.debug = debug
    def read_char(self, eof_error=True):
        if self.new == None:
            c = self.stream.read(1)
            if eof_error and not c: raise EOFError()
            if self.debug: print(c,end='')
        else:
            c = self.new
        self.old, self.new = c, None
        return c
    def unread_char(self):
        if self.old:
            self.old, self.new = None, self.old
        else:
            raise RuntimeError('Duplicate unread_char.')


python_name_translations = {
    '+'  : 'add',
    '*'  : 'mul',
    '-'  : 'sub',
    '/'  : 'div',
    '1+'  : 'inc',
    '1-'  : 'dec',
}

python_name_substitutions = {
    '-'  : '_',
    '*'  : 'O',
    '+'  : 'X',
    '<'  : 'lt',
    '<=' : 'le',
    '='  : 'sim',
    '/=' : 'ne',
    '>'  : 'gt',
    '>=' : 'ge',
}


class Symbol(LispObject):
    def __init__(self, name, package=None):
        self.name = name
        self.package = package

    def __repr__(self):
        if self.package:
            return 'Symbol("{}", "{}")'.format(self.name, self.package)
        else:
            return 'Symbol("{}")'.format(self.name)

    def __str__(self):
        return "{}:{}".format(self.package, self.name)

    def __hash__(self):
        return hash((self.name, self.package))

    def __eq__(self, other):
        return (self.name, self.package) == (other.name, other.package)

    @property
    def python_name(self):
        name = self.name
        if name in python_name_translations:
            return python_name_translations[name]
        else:
            for (old, new) in python_name_substitutions.items():
                name = name.replace(old, new)
            return name.lower()


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

    def __getitem__(self, index):
        cons = self
        for _ in range(index):
            if not cons.cdr:
                raise RuntimeError('{} is too short for index {}.'.format(self,index))
            cons = cons.cdr
        return cons.car

    def __setitem__(self, index, value):
        cons = self
        for _ in range(index):
            if not cons.cdr:
                raise RuntimeError('{} is too short for index {}.'.format(self,index))
            cons = cons.cdr
        cons.car = value

    @property
    def python_name(self):
        if self.car == Symbol('COMMON-LISP', 'SETF'):
            return 'set_' + python_name(self.cdr.car)
        else:
            raise RuntimeError('Not a function name: {}'.format(self))

    def __eq__(self, other) -> bool:
        if isinstance(other, Cons):
            return self.car == other.car and self.cdr == other.cdr
        else:
            return False


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


class LispWrapper (LispObject):
    def __init__(self, lisp, handle):
        self.lisp = lisp
        self.handle = handle

    def __del__(self):
        try:
            self.lisp.eval('#{}!'.format(self.handle))
        except:
            pass

    def __call__(self, *args, **kwargs):
        restAndKeys = [ Quote(arg) for arg in args ]
        for key, value in kwargs.items():
            restAndKeys.append(Keyword(key.upper()))
            restAndKeys.append(Quote(value))
        return self.lisp.eval(List(Symbol('FUNCALL', 'CL'), Quote(self), *restAndKeys))
