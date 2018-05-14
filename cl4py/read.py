import io
from .readtable import SyntaxType,Readtable
from .parse import parse
from .data import *

readtable = Readtable()
labels = None

# An implementation of the Common Lisp reader algorithm, with the following
# simplifications and changes:
#
# 1. Whitespace is never preserved.
# 2. READ always assumes EOF error to be true.
# 3. READTABLE-CASE is always :UPCASE.
# 4. *READ-EVAL* is always false.
# 5. *READ-BASE* is always 10.
# 6. There are no invalid characters.

def read(stream, recursive=False):
    def nextchar():
        char = stream.read(1)
        # 1. EOF processing
        if not char: raise EOFError()
        return char
    def peek():
        char = stream.read(1)
        stream.seek(stream.tell() - 1)
        return char

    while True:
        x = nextchar()

        syntax_type = readtable.syntax_type(x)
        # 3. whitespace
        if syntax_type == SyntaxType.WHITESPACE:
            continue
        # 4. macro characters
        elif (syntax_type == SyntaxType.TERMINATING_MACRO_CHARACTER or
              syntax_type == SyntaxType.NON_TERMINATING_MACRO_CHARACTER):
            value = readtable.get_macro_character(x)(stream, x)
            if value == None:
                continue
            else:
                return value
        # 5. single escape character
        elif syntax_type == SyntaxType.SINGLE_ESCAPE:
            token = [nextchar()]
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
            y = peek()
            if not y: break
            syntax_type = readtable.syntax_type(y)
            if not escape:
                # 8. even number of multiple escape characters
                if syntax_type == SyntaxType.SINGLE_ESCAPE:
                    stream.read(1)
                    token.append(nextchar())
                elif syntax_type == SyntaxType.MULTIPLE_ESCAPE:
                    escape = True
                    stream.read(1)
                elif syntax_type == SyntaxType.TERMINATING_MACRO_CHARACTER:
                    break
                elif syntax_type == SyntaxType.WHITESPACE:
                    stream.read(1)
                    break
                else:
                    token.append(stream.read(1).upper())
            else:
                # 9. odd number of multiple escape characters
                if syntax_type == SyntaxType.SINGLE_ESCAPE:
                    stream.read(1)
                    token.append(nextchar())
                elif syntax_type == SyntaxType.MULTIPLE_ESCAPE:
                    escape = False
                    stream.read(1)
                else:
                    token.append(stream.read(1))

        # 10.
        return parse(''.join(token))


def read_delimited_list(char, stream, recursive):
    def peek():
        while True:
            x = stream.read(1)
            if not x: raise EOFError()
            stream.seek(stream.tell() - 1)
            if readtable.syntax_type(x) == SyntaxType.WHITESPACE:
                stream.read(1)
            else:
                return x
    def nextchar():
        stream.read(1)

    head = Cons(None, None)
    tail = head
    while True:
        x = peek()
        if x == char:
            nextchar()
            return head.cdr
        elif x == '.':
            nextchar()
            tail.cdr = read(stream, True)
            # TODO handle errors
        else:
            cons = Cons(read(stream, True), None)
            tail.cdr = cons
            tail = cons

def left_parenthesis(stream, char):
    return read_delimited_list(')', stream, True)


def right_parenthesis(stream, char):
    raise RuntimeError('Unmatched closing parenthesis.')


def single_quote(stream, char):
    return Cons(Symbol("QUOTE", "COMMON-LISP"),
                Cons(read(stream, True), None))


readtable.set_macro_character('(', left_parenthesis)
readtable.set_macro_character(')', right_parenthesis)
readtable.set_macro_character("'", single_quote)
