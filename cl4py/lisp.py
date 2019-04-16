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
        # The name of the current package.
        self.package = "COMMON-LISP-USER"
        # Each Lisp process has its own readtable.
        self.readtable = Readtable(self)
        # The classes dict maps from symbols to python classes.
        self.classes = {}
        # Whenever the reader encounters a Lisp object whose class is not
        # yet known, it stores it in this {class_name : instances} dict.
        # This allows us to patch these instances later.
        self.unpatched_instances = {}
        # If debug is true, cl4py will print plenty of debug information.
        self.debug = False
        # Finally, check whether the user wants quicklisp to be available.
        if quicklisp:
            install_and_load_quicklisp(self)


    def __del__(self):
        try:
            self.stdin.write('(cl-user:quit)\n')
        except:
            pass


    def eval(self, expr):
        sexp = lispify(self, expr)
        if self.debug: print(sexp)
        self.stdin.write(sexp + '\n')
        pkg = self.readtable.read(self.stdout)
        val = self.readtable.read(self.stdout)
        err = self.readtable.read(self.stdout)
        msg = self.readtable.read(self.stdout)
        # Update the current package.
        self.package = pkg
        # Write the Lisp output to the Python output.
        print(msg,end='')
        # If there is an error, raise it.
        if isinstance(err, Cons):
            condition = err.car
            msg = err.cdr.car if err.cdr else ""
            def init(self):
                RuntimeError.__init__(self, msg)
            raise type(str(condition), (RuntimeError,),
                       {'__init__': init})()
        # Now, check whether there are any unpatched instances.  If so,
        # figure out their class definitions and patch them accordingly.
        items = list(self.unpatched_instances.items())
        self.unpatched_instances.clear()
        for (cls_name, instances) in items:
            cls = type(cls_name.python_name, (LispWrapper,), {})
            self.classes[cls_name] = cls
            alist = self.function('cl4py:class-information')(cls_name)
            for cons in alist:
                add_member_function(cls, cons.car, cons.cdr)
            for instance in instances:
                instance.__class__ = cls
        # Finally, return the resulting values.
        if val == ():
            return None
        elif val.cdr == ():
            return val.car
        else:
            return tuple(val)


    def find_package(self, name):
        return self.function('CL:FIND-PACKAGE')(name)


    def function(self, name):
        return self.eval( ('CL:FUNCTION', name) )


def add_member_function(cls, name, gf):
    class_name = cls.__name__
    method_name = name.python_name
    setattr(cls, method_name, lambda self, *args: gf(self, *args))


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
