import os
import re
import pytest
import cl4py
from cl4py import List, Symbol

# FIXME: should have test for quicklisp, but that would require a test
# install of QL...

@pytest.fixture()
def stock_lisp():
    return cl4py.Lisp()

@pytest.fixture()
def backtrace_lisp():
    return cl4py.Lisp(backtrace=True)

def load_sample_program(lisp_obj: cl4py.Lisp) -> None:
    cl = lisp_obj.find_package("COMMON-LISP")
    retval = cl.compile_file(
        os.path.join(os.path.dirname(__file__), "sample-program.lisp")
    )
    cl.load(retval[0])

def test_backtrace_param():
    lisp = cl4py.Lisp(backtrace=True)
    assert lisp.eval( Symbol("*BACKTRACE*", "CL4PY") )
    assert lisp.backtrace
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

def test_produce_backtrace_type_error(stock_lisp, backtrace_lisp):
    with pytest.raises(RuntimeError):
        load_sample_program(stock_lisp)
        stock_lisp.find_package("COMMON-LISP-USER").make_type_error()

    lisp = cl4py.Lisp(backtrace=True, quicklisp=True)
    load_sample_program(lisp)
    try:
        lisp.find_package("COMMON-LISP-USER").make_type_error()
    except RuntimeError as e:
        msg = e.args[0]
        backtrace_re = re.compile('Backtrace', re.MULTILINE)
        assert re.search(backtrace_re, msg)
    else:
        pytest.fail("Should have seen a RuntimeError")

def test_produce_backtrace_simple_error(stock_lisp, backtrace_lisp):
    with pytest.raises(RuntimeError):
        load_sample_program(stock_lisp)
        stock_lisp.find_package("COMMON-LISP-USER").make_error()


    load_sample_program(backtrace_lisp)
    try:
        backtrace_lisp.find_package("COMMON-LISP-USER").make_error()
    except RuntimeError as e:
        msg = e.args[0]
        backtrace_re = re.compile('Backtrace', re.MULTILINE)
        assert re.search(backtrace_re, msg)
    else:
        pytest.fail("Should have seen a RuntimeError")
