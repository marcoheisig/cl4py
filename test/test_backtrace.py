import pytest
import cl4py
from cl4py import List, Symbol

def test_backtrace_param():
    lisp = cl4py.Lisp(backtrace=True)
    assert lisp.eval( Symbol("*BACKTRACE*", "CL4PY") )
    lisp = cl4py.Lisp(backtrace=False)
    assert not lisp.eval( Symbol("*BACKTRACE*", "CL4PY"))
