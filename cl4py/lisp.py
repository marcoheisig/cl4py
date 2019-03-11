import subprocess
import io
import importlib.machinery
import importlib.util
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


    def load(self, file):
        return self.eval(List(Symbol('LOAD', 'CL'), Quote(file)))


    def find_package(self, name):
        spec = importlib.machinery.ModuleSpec(name, None)
        module = importlib.util.module_from_spec(spec)
        query = ('loop', 'for', 'symbol', 'being', 'each', 'external-symbol', 'of', Quote(name),
                 'when', ('fboundp', 'symbol'),
                 'unless', ('special-operator-p', 'symbol'),
                 'unless', ('macro-function', 'symbol'),
                 'collect', ('Cons',
                             ('symbol-name', 'symbol'),
                             ('symbol-function', 'symbol')))

        def pythonize(name):
            name = name.replace('-', '_')
            if name.isupper():
                name = name.lower()
            return name

        for cons in self.eval(query):
            if isinstance(cons.car, str):
                setattr(module, pythonize(cons.car), cons.cdr)
        return module
