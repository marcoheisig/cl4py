import subprocess
import os
import io
import importlib
from .data import *
from .read import Readtable


def pythonize(name):
    name = name.replace('-', '_')
    if name.isupper():
        name = name.lower()
    return name


class Lisp:
    def __init__(self, cmd=['sbcl', '--script']):
        p = subprocess.Popen(cmd + [os.path.dirname(__file__) + "/py.lisp"],
                             stdin = subprocess.PIPE,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE,
                             shell = False)
        self.stdin = io.TextIOWrapper(p.stdin, write_through=True,
                                      line_buffering=1,
                                      encoding='utf-8')
        self.stdout = io.TextIOWrapper(p.stdout, encoding='utf-8')
        self.foreign_objects = {}
        self.readtable = Readtable(self)


    def __del__(self):
        try:
            self.stdin.write('(quit)\n')
        except:
            pass


    def eval(self, expr):
        self.stdin.write(sexp(expr) + '\n')
        val = self.readtable.read(self.stdout)
        err = self.readtable.read(self.stdout)
        if err:
            condition = err.car
            msg = err.cdr.car.data if err.cdr else ""
            def init(self):
                RuntimeError.__init__(self, msg)
            raise type(condition, (RuntimeError,),
                       {'__init__': init})()
        return val


    def load(self, file):
        return self.eval(List('CL:LOAD', String(file)))


    def find_package(self, name):
        spec = importlib.machinery.ModuleSpec(name, None)
        module = importlib.util.module_from_spec(spec)
        query = List('loop', 'for', 'symbol', 'being', 'each', 'external-symbol', 'of', String(name),
                     'when', List('fboundp', 'symbol'),
                     'unless', List('special-operator-p', 'symbol'),
                     'unless', List('macro-function', 'symbol'),
                     'collect', List('Cons',
                                     List('symbol-name', 'symbol'),
                                     List('symbol-function', 'symbol')))
        for cons in self.eval(query):
            if isinstance(cons.car, String):
                setattr(module, pythonize(cons.car.data), cons.cdr)
        return module
