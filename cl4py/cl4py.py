import subprocess
import os
import io
from .data import sexp
from .read import read

package = 'COMMON-LISP-USER'


class Lisp:
    def __init__(self):
        cl4py = os.path.dirname(__file__) + "/cl4py.lisp"
        cmd = ['/usr/local/bin/sbcl', '--script', cl4py]
        p = subprocess.Popen(cmd,
                             stdin = subprocess.PIPE,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE,
                             shell = False)
        self.stdin = io.TextIOWrapper(p.stdin, write_through=True,
                                      line_buffering=1,
                                      encoding='utf-8')
        self.stdout = io.TextIOWrapper(p.stdout, encoding='utf-8')

    def eval(self, expr):
        global package
        self.stdin.write(sexp(expr) + '\n')
        val, err, package = read(self.stdout), read(self.stdout), read(self.stdout)
        if err: raise RuntimeError(str(err))
        return val
