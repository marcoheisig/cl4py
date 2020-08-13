from pytest import fixture
import cl4py
import os

# pytest forces violation of this pylint rule
# pylint: disable=redefined-outer-name


@fixture(scope="module")
def lisp():
    return cl4py.Lisp()


@fixture(scope="module")
def cl(lisp):
    return lisp.function("find-package")("CL")


# This test verifies issue underlying MR #9
def test_readtable_problem(cl):
    retval = cl.compile_file(
        os.path.join(os.path.dirname(__file__), "sample-program.lisp")
    )
    outfile = os.path.join(os.path.dirname(__file__), "sample-program.fasl")
    try:
        assert retval[0] == outfile
        assert os.path.exists(retval[0])
        assert retval[1] == ()
        assert retval[2] == ()
    finally:
        cleanup(outfile)
    cleanup(outfile)

def cleanup(outfile):
    if os.path.exists(outfile):
        try:
            os.remove(outfile)
        except:                 # pylint: disable=bare-except
            pass
