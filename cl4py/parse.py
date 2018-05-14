import re
from .data import *
from fractions import Fraction

exponent_markers = 'DdEdFfLlSs'
integer_regex = re.compile(r"[+-]?[0-9]+\.?")
ratio_regex = re.compile(r"([+-]?[0-9]+)/([0-9]+)")
float_regex = re.compile(r"[+-]?[0-9]*\.[0-9]+")
symbol_regex = re.compile(r"([^:]+(::?))?([^:]+)")

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
        # TODO handle exponent markers
        return float(token)
    m = re.fullmatch(symbol_regex, token)
    if m:
        package = m.group(1) or "COMMON-LISP-USER"
        delimiter = m.group(2) or ":"
        name = m.group(3)
        return Symbol(name, package)

    raise RuntimeError('Failed to parse token "' + token + '".')
