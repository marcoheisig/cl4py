import io
from enum import Enum

SyntaxType = Enum('SyntaxType',
                  ['CONSTITUENT',
                   'TERMINATING_MACRO_CHARACTER',
                   'NON_TERMINATING_MACRO_CHARACTER',
                   'SINGLE_ESCAPE',
                   'INVALID',
                   'MULTIPLE_ESCAPE',
                   'WHITESPACE'])


class Readtable:
    def __init__(self):
        self.macro_characters = {}


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
