import io
import re
from enum import Enum
from .data import *

# An implementation of the Common Lisp reader algorithm, with the following
# simplifications and changes:
#
# 1. Whitespace is never preserved.
# 2. READ always assumes EOF error to be true.
# 3. READTABLE-CASE is always :UPCASE.
# 4. *READ-EVAL* is always false.
# 5. *READ-BASE* is always 10.
# 6. There are no invalid characters.

class Stream:
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
        self.set_macro_character("'", single_quote)
        self.set_macro_character('"', double_quote)
        self.set_macro_character('#', sharpsign)
        self.set_dispatch_macro_character('#', '\\', sharpsign_backslash)
        self.set_dispatch_macro_character('#', '(', sharpsign_left_parenthesis)
        self.set_dispatch_macro_character('#', '?', sharpsign_questionmark)
        self.set_dispatch_macro_character('#', 'A', sharpsign_a)


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
        elif c in '"\'(),;`':
            return SyntaxType.TERMINATING_MACRO_CHARACTER
        else:
            return SyntaxType.CONSTITUENT


    def read_from_string(self, string):
        return self.read(io.StringIO(string))


    def read(self, stream, recursive=False):
        if not isinstance(stream, Stream):
            stream = Stream(stream)
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
                if value == None:
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
            return parse(''.join(token))


    def read_delimited_list(self, delim, stream, recursive):
        def skip_whitespace():
            while True:
                x = stream.read_char()
                if self.syntax_type(x) != SyntaxType.WHITESPACE:
                    stream.unread_char()
                    break

        head = Cons(None, None)
        tail = head
        while True:
            skip_whitespace()
            x = stream.read_char()
            if x == delim:
                return head.cdr
            elif x == '.':
                tail.cdr = self.read(stream, True)
                # TODO handle errors
            else:
                stream.unread_char()
                cons = Cons(self.read(stream, True), None)
                tail.cdr = cons
                tail = cons


def left_parenthesis(r, s, c):
    return r.read_delimited_list(')', s, True)


def right_parenthesis(r, s, c):
    raise RuntimeError('Unmatched closing parenthesis.')


def single_quote(r, s, c):
    return Cons("COMMON-LISP:QUOTE", Cons(r.read(s, True), None))


def double_quote(r, s, c):
    result = ''
    while True:
        c = s.read_char()
        if c == '"':
            return String(result)
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


def sharpsign_backslash(r, s, c, n):
    # TODO
    return s.read_char()


def sharpsign_left_parenthesis(r, s, c, n):
    return list(r.read_delimited_list(")", s, True))


def sharpsign_questionmark(r, s, c, n):
    try:
        return r.lisp.foreign_objects[n]
    except:
        obj = LispObject(r.lisp, n)
        r.lisp.foreign_objects[n] = obj
        return obj


def sharpsign_a(r, s, c, n):
    # TODO
    return
