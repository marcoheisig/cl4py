'''
Correspondence of Python types and Lisp types in cl4py:

| Python             | Lisp          | Comment                                |
|--------------------+---------------+----------------------------------------|
| True, False        | T, NIL        |                                        |
| None               | NIL           |                                        |
| int                | integer       |                                        |
| float              | double-float  |                                        |
| complex            | (complex *)   |                                        |
| string             | string        |                                        |
| list               | simple-vector |                                        |
| tuple              | simple-vector | cl4py converts simple-vectors to lists |
| range              | -             |                                        |
| dict               | hash-table    |                                        |
| cl4py.Cons         | cons          |                                        |
| cl4py.Symbol       | symbol        |                                        |
| cl4py.Package      | package       |                                        |
| fractions.Fraction | ratio         |                                        |
| numpy.array        | array         |                                        |

'''

def string(x):
    if isinstance(x, str):
        return x
    elif isinstance(x, Symbol):
        return x.name
    else:
        raise TypeError('Not a valid string designator: ' + str(x) + '.')

def package(x):
    if isinstance(x, Package):
        return x
    elif isinstance(x, str):
        return Package(x)
    elif isinstance(x, Symbol):
        return Package(x.name)
    else:
        raise TypeError('Not a valid package designator: ' + str(x) + '.')


class Cons:
   def __init__(self, car, cdr):
       self.car = car
       self.cdr = cdr


class Symbol:
    def __init__(self, name, package):
        self.name = string(name)
        self.package = Package(package)


class Package:
    def __init__(self, name):
        self.name = string(name)
