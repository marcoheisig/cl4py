import re
import os
import numpy
import importlib.machinery
import importlib.util
from fractions import Fraction
from enum import Enum
from .data import *
from .circularity import *

# An implementation of the Common Lisp reader algorithm, with the following
# simplifications and changes:
#
# 1. Whitespace is never preserved.
# 2. READ always assumes EOF error to be true.
# 3. READTABLE-CASE is always :UPCASE.
# 4. *READ-EVAL* is always false.
# 5. *READ-BASE* is always 10.
# 6. *READ-DEFAULT-FORMAT* is always SINGLE-FLOAT.
# 7. There are no invalid characters.
# 8. The input is assumed to be well formed.

integer_regex = re.compile(r"[+-]?[0-9]+\.?")
ratio_regex = re.compile(r"([+-]?[0-9]+)/([0-9]+)")
float_regex = re.compile(r"([+-]?[0-9]+(?:\.[0-9]+)?)(?:([eEsSfFdDlL])([0-9]+))?")
symbol_regex = re.compile(r"(?:([^:]*?)(::?))?([^:]+)")

SyntaxType = Enum('SyntaxType',
                  ['CONSTITUENT',
                   'TERMINATING_MACRO_CHARACTER',
                   'NON_TERMINATING_MACRO_CHARACTER',
                   'SINGLE_ESCAPE',
                   'INVALID',
                   'MULTIPLE_ESCAPE',
                   'WHITESPACE'])


class Readtable:
    def __init__(self, lisp):
        self.lisp = lisp
        self.macro_characters = {}
        self.set_macro_character('(', left_parenthesis)
        self.set_macro_character(')', right_parenthesis)
        self.set_macro_character('{', left_curly_bracket)
        self.set_macro_character('}', right_curly_bracket)
        self.set_macro_character("'", single_quote)
        self.set_macro_character('"', double_quote)
        self.set_macro_character('#', sharpsign)
        self.set_dispatch_macro_character('#', '\\', sharpsign_backslash)
        self.set_dispatch_macro_character('#', "'", sharpsign_single_quote)
        self.set_dispatch_macro_character('#', '(', sharpsign_left_parenthesis)
        self.set_dispatch_macro_character('#', '?', sharpsign_questionmark)
        self.set_dispatch_macro_character('#', 'A', sharpsign_a)
        self.set_dispatch_macro_character('#', 'C', sharpsign_c)
        self.set_dispatch_macro_character('#', 'M', sharpsign_m)
        self.set_dispatch_macro_character('#', 'N', sharpsign_n)
        self.set_dispatch_macro_character('#', '=', sharpsign_equal)
        self.set_dispatch_macro_character('#', '#', sharpsign_sharpsign)


    def get_macro_character(self, char):
        return self.macro_characters[char]


    def set_macro_character(self, char, fn):
        self.macro_characters[char] = fn


    def get_dispatch_macro_character(self, dchar, schar):
        return self.macro_characters[(dchar, schar)]


    def set_dispatch_macro_character(self, dchar, schar, f):
        self.macro_characters[(dchar, schar)] = f


    def syntax_type(self, c):
        if c.isspace():
            return SyntaxType.WHITESPACE
        elif c == '\\':
            return SyntaxType.SINGLE_ESCAPE
        elif c == '#':
            return SyntaxType.NON_TERMINATING_MACRO_CHARACTER
        elif c == '|':
            return SyntaxType.MULTIPLE_ESCAPE
        elif c in '"\'(),;`{}[]<>':
            return SyntaxType.TERMINATING_MACRO_CHARACTER
        else:
            return SyntaxType.CONSTITUENT


    def read(self, stream, recursive=False):
        if not isinstance(stream, Stream):
            stream = Stream(stream)
        value = self.read_aux(stream)
        if recursive:
            return value
        else:
            return circularize(value)


    def read_aux(self, stream):
        while True:
            # 1. read one character
            x = stream.read_char()
            syntax_type = self.syntax_type(x)
            # 3. whitespace
            if syntax_type == SyntaxType.WHITESPACE:
                continue
            # 4. macro characters
            elif (syntax_type == SyntaxType.TERMINATING_MACRO_CHARACTER or
                  syntax_type == SyntaxType.NON_TERMINATING_MACRO_CHARACTER):
                value = self.get_macro_character(x)(self, stream, x)
                if value is None:
                    continue
                else:
                    return value
            # 5. single escape character
            elif syntax_type == SyntaxType.SINGLE_ESCAPE:
                token = [stream.read_char()]
                escape = False
            # 6. multiple escape character
            elif syntax_type == SyntaxType.MULTIPLE_ESCAPE:
                token = []
                escape = True
            # 7. constituent character
            else:
                token = [x.upper()]
                escape = False

            while True:
                y = stream.read_char(False)
                if not y: break
                syntax_type = self.syntax_type(y)
                if not escape:
                    # 8. even number of multiple escape characters
                    if syntax_type == SyntaxType.SINGLE_ESCAPE:
                        token.append(stream.read_char())
                    elif syntax_type == SyntaxType.MULTIPLE_ESCAPE:
                        escape = True
                    elif syntax_type == SyntaxType.TERMINATING_MACRO_CHARACTER:
                        stream.unread_char()
                        break
                    elif syntax_type == SyntaxType.WHITESPACE:
                        stream.unread_char()
                        break
                    else:
                        token.append(y.upper())
                else:
                    # 9. odd number of multiple escape characters
                    if syntax_type == SyntaxType.SINGLE_ESCAPE:
                        token.append(stream.read_char())
                    elif syntax_type == SyntaxType.MULTIPLE_ESCAPE:
                        escape = False
                    else:
                        token.append(y)
            # 10.
            return self.parse(''.join(token))


    def parse(self, token):
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
            base = m.group(1)
            exponent_marker = m.group(2)
            exponent = m.group(3)
            if not exponent_marker:
                return numpy.float32(base) * (numpy.float32(10) ** numpy.float32(exponent))
            elif exponent_marker in 'sS':
                return numpy.float16(base) * (numpy.float16(10) ** numpy.float16(exponent))
            elif exponent_marker in 'eEfF':
                return numpy.float32(base) * (numpy.float32(10) ** numpy.float32(exponent))
            elif exponent_marker in 'dD':
                return numpy.float64(base) * (numpy.float64(10) ** numpy.float64(exponent))
            elif exponent_marker in 'lL':
                return numpy.float128(base) * (numpy.float128(10) ** numpy.float128(exponent))
        # symbol
        m = re.fullmatch(symbol_regex, token)
        if m:
            package = m.group(1)
            delimiter = m.group(2)
            name = m.group(3)
            if not package:
                if delimiter:
                    return Keyword(name)
                else:
                    return Symbol(name, self.lisp.package)
            else:
                if package in ['CL', 'COMMON-LISP']:
                    if name == 'T': return True
                    if name == 'NIL': return ()
                return Symbol(name, package)
        raise RuntimeError('Failed to parse token "' + token + '".')



    def read_delimited_list(self, delim, stream, recursive):
        def skip_whitespace():
            while True:
                x = stream.read_char()
                if self.syntax_type(x) != SyntaxType.WHITESPACE:
                    stream.unread_char()
                    break

        head = Cons((), ())
        tail = head
        while True:
            skip_whitespace()
            x = stream.read_char()
            if x == delim:
                return head.cdr
            elif x == '.':
                tail.cdr = self.read(stream, True)
            else:
                stream.unread_char()
                cons = Cons(self.read(stream, True), ())
                tail.cdr = cons
                tail = cons


def left_parenthesis(r, s, c):
    return r.read_delimited_list(')', s, True)


def right_parenthesis(r, s, c):
    raise RuntimeError('Unmatched closing parenthesis.')


def left_curly_bracket(r, s, c):
    table = {}
    data = r.read_delimited_list('}', s, True)
    while data:
        key = car(data)
        rest = cdr(data)
        if null(rest):
            raise RuntimeError('Odd number of hash table data.')
        value = car(rest)
        table[key] = value
        data = cdr(rest)
    return table


def right_curly_bracket(r, s, c):
    raise RuntimeError('Unmatched closing curly bracket.')


def single_quote(r, s, c):
    return Cons("COMMON-LISP:QUOTE", Cons(r.read(s, True), None))


def double_quote(r, s, c):
    result = ''
    while True:
        c = s.read_char()
        if c == '"':
            return result
        elif c == '\\':
            result += s.read_char()
        else:
            result += c


def semicolon(r, s, c):
    while s.read_char() != '\n': pass


def sharpsign(r, s, c):
    digits = ''
    while True:
        c = s.read_char()
        if c.isdigit():
            digits += c
        else:
            c = c.upper()
            break
    n = int(digits) if digits else 0
    return r.get_dispatch_macro_character('#', c)(r, s, c, n)


character_names = {
    'NEWLINE'   : '\x0A',
    'SPACE'     : '\x20',
    'RUBOUT'    : '\x7F',
    'PAGE'      : '\x0C',
    'TAB'       : '\x09',
    'BACKSPACE' : '\x08',
    'RETURN'    : '\x0D',
    'LINEFEED'  : '\x0A',
}


def sharpsign_backslash(r, s, c, n):
    token = [s.read_char()]
    while True:
        c = s.read_char()
        if c.isalpha():
            token.append(c)
        else:
            s.unread_char()
            break
    if len(token) == 1:
        return token[0]
    else:
        key = ''.join(token).upper()
        if key in character_names:
            return character_names[key]
        else:
            raise RuntimeError('Not a valid character name: {}'.format('key'))


def sharpsign_single_quote(r, s, c, n):
    return List('CL:FUNCTION', r.read(s, True))


def sharpsign_left_parenthesis(r, s, c, n):
    l = r.read_delimited_list(")", s, True)
    if not l:
        return []
    else:
        return list(l)


def sharpsign_questionmark(r, s, c, n):
    try:
        return r.lisp.foreign_objects[n]
    except:
        obj = LispWrapper(r.lisp, n)
        r.lisp.foreign_objects[n] = obj
        return obj


def sharpsign_a(r, s, c, n):
    L = r.read(s, True)
    def listify(L, n):
        if n == 0:
            return L
        elif n == 1:
            return list(L)
        else:
            return [listify(l,n-1) for l in L]
    return numpy.array(listify(L, n))


def sharpsign_c(r, s, c, n):
    (real, imag) =  list(r.read(s, True))
    return complex(real, imag)


pythonizers = {
    '<'  : 'lt',
    '<=' : 'le',
    '='  : 'sim',
    '>'  : 'gt',
    '>=' : 'ge',
    '+'  : 'add',
    '*'  : 'mul',
    '-'  : 'sub',
    'i'  : 'div',
}


def pythonize(name):
    if name in pythonizers:
        return pythonizers[name]
    else:
        return name.replace('-', '_').lower()


def sharpsign_m(r, s, c, n):
    data = r.read(s)
    name, alist = data.car, data.cdr
    spec = importlib.machinery.ModuleSpec(name, None)
    module = importlib.util.module_from_spec(spec)
    module.__class__ = Package

    for cons in alist:
        setattr(module, pythonize(cons.car), cons.cdr)
    return module

def sharpsign_equal(r, s, c, n):
    value = r.read(s, True)
    return SharpsignEquals(n, value)


def sharpsign_sharpsign(r, s, c, n):
    return SharpsignSharpsign(n)


def sharpsign_n(r, s, c, n):
    f = r.read(s, True)
    A = numpy.load(f)
    os.remove(f)
    return A

