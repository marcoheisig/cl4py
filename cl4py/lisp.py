import subprocess
import os
import io
from .data import sexp
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
        self.readtable = Readtable()

    def eval(self, expr):
        self.stdin.write(sexp(expr) + '\n')
        val = self.readtable.read(self.stdout)
        err = self.readtable.read(self.stdout)
        if err: raise RuntimeError(str(err))
        return val
