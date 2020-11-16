import pytest
import cl4py
from cl4py import List, Symbol

def test_backtrace_param():
    lisp = cl4py.Lisp(backtrace=True)
    assert lisp.eval( Symbol("*BACKTRACE*", "CL4PY") )
    assert lisp.backtrace
    assert lisp.find_package("TRIVIAL-BACKTRACE")
    lisp = cl4py.Lisp(backtrace=False)
    assert not lisp.eval( Symbol("*BACKTRACE*", "CL4PY"))
    assert not lisp.backtrace

def test_backtrace_setting():
    lisp = cl4py.Lisp(backtrace=True)
    assert lisp.eval( Symbol("*BACKTRACE*", "CL4PY") )
    assert lisp.backtrace
    lisp.backtrace = False
    assert not lisp.eval( Symbol("*BACKTRACE*", "CL4PY"))
    assert not lisp.backtrace

    lisp = cl4py.Lisp(backtrace=False)
    assert not lisp.eval( Symbol("*BACKTRACE*", "CL4PY") )
    assert not lisp.backtrace
    lisp.backtrace = True
    assert lisp.eval( Symbol("*BACKTRACE*", "CL4PY"))
    assert lisp.backtrace
    assert lisp.find_package("TRIVIAL-BACKTRACE")
