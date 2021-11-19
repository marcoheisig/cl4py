import os
import pytest
import fractions

from pytest import fixture
import cl4py
from cl4py import List, Symbol

# pytest forces violation of this pylint rule
# pylint: disable=redefined-outer-name

@fixture(scope="module")
def lisp():
    return cl4py.Lisp()


@fixture(scope="module")
def cl(lisp):
    return lisp.find_package("CL")


def test_startup(lisp):
    assert isinstance(lisp, cl4py.Lisp)


def test_examples(lisp):
    assert lisp.eval( 42 ) == 42
    assert lisp.eval(("+", 2, 3)) == 5
    assert lisp.eval( ('/', ('*', 3, 5), 2) ) == fractions.Fraction(15, 2)
    assert lisp.eval( cl4py.List(cl4py.Symbol('STRING='), 'foo', 'bar') ) == ()
    assert lisp.eval( cl4py.List(cl4py.Symbol('STRING='), 'foo', 'foo') ) == True
    assert lisp.eval(cl4py.Symbol('*PRINT-BASE*', 'COMMON-LISP')) == 10
    assert lisp.eval( ('loop', 'for', 'i', 'below', 5, 'collect', 'i') ) == cl4py.List(0, 1, 2, 3, 4)
    assert lisp.eval( ('with-output-to-string', ('stream',),
                       ('princ', 12, 'stream'),
                       ('princ', 34, 'stream')) ) == '1234'


def test_finding_functions(lisp, cl):
    add = lisp.function("+")
    assert add(1, 2, 3, 4) == 10
    div = lisp.function("/")
    assert div(2, 4) == fractions.Fraction(1, 2)
    assert cl.oddp(5)
    assert cl.cons(5, None) == cl4py.List(5)
    assert cl.remove(5, [1, -5, 2, 7, 5, 9], key=cl.abs) == [1, 2, 7, 9]
    assert cl.mapcar(cl.constantly(4), (1, 2, 3)) == cl4py.List(4, 4, 4)
    assert cl.loop('repeat', 5, 'collect', 42) == List(42, 42, 42, 42, 42)
    assert cl.progn(5, 6, 7, ('+', 4, 4)) == 8


def test_pythony_names(cl):
    assert cl.type_of("foo") == List(
        Symbol("SIMPLE-ARRAY", "COMMON-LISP"),
        Symbol("CHARACTER", "COMMON-LISP"),
        List(3),
    )
    assert cl.add(2,3,4,5) == 14
    assert cl.stringgt('baz', 'bar') == 2
    assert cl.print_base == 10
    assert cl.MOST_POSITIVE_DOUBLE_FLOAT == 1.7976931348623157e+308


def test_conses(cl, lisp):
    assert lisp.eval(("CONS", 1, 2)) == cl4py.Cons(1, 2)
    lst = lisp.eval(("CONS", 1, ("CONS", 2, ())))
    assert lst == cl4py.List(1, 2)
    assert lst.car == 1
    assert lst.cdr == cl4py.List(2)
    assert list(lst) == [1, 2]
    assert sum(lst) == 3
    assert lisp.eval( ('CONS', 1, ('CONS', 2, 3 )) ) == cl4py.DottedList(1, 2, 3)
    twos = cl.cons(2, 2)
    twos.cdr = twos
    assert cl.mapcar(lisp.function("+"), (1, 2, 3, 4), twos) == List(3, 4, 5, 6)


def test_error(cl, lisp):
    retval = cl.compile_file(
        os.path.join(os.path.dirname(__file__), "sample-program.lisp")
    )
    cl.load(retval[0])
    with pytest.raises(RuntimeError):
        lisp.eval( ("CL-USER::MAKE-ERROR", ))
