from pytest import fixture
import fractions

import cl4py
from cl4py import List, Symbol

# pytest forces violation of this pylint rule
# pylint: disable=redefined-outer-name

@fixture(scope="module")
def lisp():
    return cl4py.Lisp()


@fixture(scope="module")
def cl(lisp):
    return lisp.function("find-package")("CL")


def test_startup(lisp):
    assert isinstance(lisp, cl4py.Lisp)


def test_examples(lisp):
    assert lisp.eval(("+", 2, 3)) == 5
    add = lisp.function("+")
    assert add(1, 2, 3, 4) == 10
    div = lisp.function("/")
    assert div(2, 4) == fractions.Fraction(1, 2)
    assert lisp.eval(cl4py.Symbol("*PRINT-BASE*", "COMMON-LISP")) == 10
    assert lisp.eval(("CONS", 1, 2)) == cl4py.Cons(1, 2)
    lst = lisp.eval(("CONS", 1, ("CONS", 2, ())))
    assert lst == cl4py.List(1, 2)
    assert lst.car == 1
    assert lst.cdr == cl4py.List(2)
    assert list(lst) == [1, 2]
    assert sum(lst) == 3


def test_finding_functions(cl):
    assert cl.oddp(5)
    assert cl.cons(5, None) == cl4py.List(5)
    assert cl.remove(5, [1, -5, 2, 7, 5, 9], key=cl.abs) == [1, 2, 7, 9]


def test_pythony_names(cl):
    assert cl.type_of("foo") == List(
        Symbol("SIMPLE-ARRAY", "COMMON-LISP"),
        Symbol("CHARACTER", "COMMON-LISP"),
        List(3),
    )


def test_higher_order(cl):
    assert cl.mapcar(cl.constantly(4), (1, 2, 3)) == List(4, 4, 4)


def test_circular_objects(cl, lisp):
    twos = cl.cons(2, 2)
    twos.cdr = twos
    assert cl.mapcar(lisp.function("+"), (1, 2, 3, 4), twos) == \
        List(3, 4, 5, 6)
