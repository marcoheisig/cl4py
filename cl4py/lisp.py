import subprocess
import os
import io
import importlib
from .data import *
from .read import Readtable

class Lisp:
    def __init__(self):
        cmd = ['/usr/local/bin/sbcl', '--script', os.path.dirname(__file__) + "/py.lisp"]
        p = subprocess.Popen(cmd,
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
        if err: raise RuntimeError(str(err))
        return val


    def register(self, name):
        spec = importlib.machinery.ModuleSpec(name, None)
        module = importlib.util.module_from_spec(spec)
        query = List('loop', 'for', 'symbol', 'being', 'each', 'external-symbol', 'of', String(name),
                     'when', List('fboundp', 'symbol'),
                     'collect', List('Cons',
                                     List('symbol-name', 'symbol'),
                                     List('symbol-function', 'symbol')))
        for cons in self.eval(query):
            if isinstance(cons.car, String):
                name = cons.car.data
                if name.isupper():
                    name = name.lower()
                setattr(module, name, cons.cdr)
        return module
