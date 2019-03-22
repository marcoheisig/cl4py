import subprocess
import io
import os.path
import urllib.request
import tempfile
from pkg_resources import resource_filename
from .data import *
from .reader import Readtable
from .writer import lispify


class Lisp:
    def __init__(self, cmd=['sbcl', '--script'], quicklisp=False):
        p = subprocess.Popen(cmd + [resource_filename(__name__, 'py.lisp')],
                             stdin = subprocess.PIPE,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE,
                             shell = False)
        self.stdin = io.TextIOWrapper(p.stdin, write_through=True,
                                      line_buffering=1,
                                      encoding='utf-8')
        self.stdout = io.TextIOWrapper(p.stdout, encoding='utf-8')
        self.foreign_objects = {}
        self.package = "COMMON-LISP-USER"
        self.readtable = Readtable(self)

        if quicklisp: install_and_load_quicklisp(self)


    def __del__(self):
        try:
            self.stdin.write('(quit)\n')
        except:
            pass


    def eval(self, expr):
        sexp = lispify(self, expr)
        self.stdin.write(sexp + '\n')
        pkg = self.readtable.read(self.stdout)
        self.package = pkg
        val = self.readtable.read(self.stdout)
        err = self.readtable.read(self.stdout)
        msg = self.readtable.read(self.stdout)
        print(msg,end='')
        if isinstance(err, Cons):
            condition = car(err)
            msg = car(cdr(err)) if cdr(err) else ""
            def init(self):
                RuntimeError.__init__(self, msg)
            raise type(str(condition), (RuntimeError,),
                       {'__init__': init})()
        return val


    def find_package(self, name):
        return self.function('CL:FIND-PACKAGE')(name)


    def function(self, name):
        return self.eval( ('CL:FUNCTION', name) )


def install_and_load_quicklisp(lisp):
    quicklisp_setup = os.path.expanduser('~/quicklisp/setup.lisp')
    if os.path.isfile(quicklisp_setup):
        lisp.function('cl:load')(quicklisp_setup)
    else:
        install_quicklisp(lisp)


def install_quicklisp(lisp):
    import urllib
    url = 'https://beta.quicklisp.org/quicklisp.lisp'
    with tempfile.NamedTemporaryFile(prefix='quicklisp-', suffix='.lisp') as tmp:
        with urllib.request.urlopen(url) as u:
            tmp.write(u.read())
        lisp.function('cl:load')(tmp.name)
    print('Installing Quicklisp...')
    lisp.eval( ('quicklisp-quickstart:install',) )
