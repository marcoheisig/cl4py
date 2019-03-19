import subprocess
import io
from pkg_resources import resource_filename
from .data import *
from .reader import Readtable
from .writer import lispify


class Lisp:
    def __init__(self, cmd=['sbcl', '--script']):
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

