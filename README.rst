cl4py - Common Lisp for Python
==============================

The library cl4py (pronounce as *clappy*) allows Python programs to call
Common Lisp libraries.  Its official mascot is the cl4py-bird:

.. image:: ./cl4py.png

Motivation
----------

You are a Python programmer, but you want access to some of the powerful
features of Lisp, for example to compile code at run time?  Or you want to
use some `awesome Lisp libraries <http://codys.club/awesome-cl/>`_?  Or
you are a Lisp programmer and want to show your work to your Python
friends.  In all these cases, cl4py is here to help you.

Tutorial
--------

You can start any number of Lisp subprocesses within Python, like this:

.. code:: python

    >>> import cl4py
    >>> lisp = cl4py.Lisp()

Of course, this requires you have some Lisp installed. If not, use
something like ``apt install sbcl``, ``pacman -S sbcl`` or ``brew install
sbcl`` to correct this deficiency.  Once you have a running Lisp process,
you can execute Lisp code on it:

.. code:: python

    # In Lisp, numbers evaluate to themselves.
    >>> lisp.eval( 42 )
    42

    # ('+', 2, 3) is a short notation for cl4py.List(cl4py.Symbol('+'), 2, 3).
    # For convenience, whenever a Python tuple is converted to Lisp
    # data, any strings therein are automatically converted to Lisp symbols.
    >>> lisp.eval( ('+', 2, 3) )
    5

    # Nested expressions are allowed, too.
    >>> lisp.eval( ('/', ('*', 3, 5), 2) )
    Fraction(15, 2)

    # Use cl4py.List instead of tuples to avoid the automatic conversion of
    # strings to symbols.
    >>> lisp.eval( cl4py.List(cl4py.Symbol('STRING='), 'foo', 'bar') )
    ()
    >>> lisp.eval( cl4py.List(cl4py.Symbol('STRING='), 'foo', 'foo') )
    True

    # Here is how you can lookup a symbol's value:
    >>> lisp.eval(cl4py.Symbol('*PRINT-BASE*', 'COMMON-LISP'))
    10

    # Of course you can also use Lisp macros:
    >>> lisp.eval( ('loop', 'for', 'i', 'below', 5, 'collect', 'i') )
    List(0, 1, 2, 3, 4)

    >>> lisp.eval( ('with-output-to-string', ('stream',),
                      ('princ', 12, 'stream'),
                      ('princ', 34, 'stream')) )
    '1234'

A cl4py.Lisp object not only provides ``eval``, but also methods for
looking up functions and packages:

.. code:: python

    >>> add = lisp.function('+')
    >>> add(1, 2, 3, 4)
    10

    >>> div = lisp.function('/')
    >>> div(2, 4)
    Fraction(1, 2)

    # Lisp packages are automatically converted to Python modules.
    >>> cl = lisp.find_package('CL')
    >>> cl.oddp(5)
    True

    >>> cl.cons(5, None)
    List(5)

    >>> cl.remove(5, [1, -5, 2, 7, 5, 9], key=cl.abs)
    [1, 2, 7, 9]

    # Higher-order functions work, too!
    >>> cl.mapcar(cl.constantly(4), (1, 2, 3))
    List(4, 4, 4)

    # cl4py even supports macros and special forms as a thin
    # wrapper around lisp.eval.
    >>> cl.loop('repeat', 5, 'collect', 42)
    List(42, 42, 42, 42, 42)

    >>> cl.progn(5, 6, 7, ('+', 4, 4))
    8

When converting Common Lisp packages to Python modules, we run into the
problem that not every Common Lisp symbol name is a valid Python
identifier.  As a remedy, so we attempt to substitute problematic
characters and symbols with something that Python can digest.  Here you can
see this substitution rules in action:

.. code:: python

    # hyphens are turned into underscores
    >>> cl.type_of("foo")
    List(Symbol("SIMPLE-ARRAY", "COMMON-LISP"), Symbol("CHARACTER", "COMMON-LISP"), List(3))

    # The functions +, -, *, /, 1+, and 1- are renamed to add, sub,
    # mul, div, inc, and dec, respectively.
    >>> cl.add(2,3,4,5)
    14

    # Within a string, occurrences of -, *, +, <=, <, =, /=, >=, gt, and ~,
    # are replaced by _, O, X, le, lt, sim, ne, ge, ge, gt, and tilde, respectively.
    >>> cl.stringgt('baz', 'bar')
    2

    # Earmuffs are stripped
    >>> cl.print_base
    10

    # Constants are capitalized
    >>> cl.MOST_POSITIVE_DOUBLE_FLOAT
    1.7976931348623157e+308

The cl4py module provides a Cons class that mimics cons cells in Lisp.

.. code:: python

    >>> lisp.eval( ('CONS', 1, 2) )
    Cons(1, 2)

    >>> lst = lisp.eval( ('CONS', 1, ('CONS', 2, () )) )
    List(1, 2)
    >>> lst.car
    1
    >>> lst.cdr
    List(2) # an abbreviation for Cons(2, ())

    # cl4py Conses are iterable!
    >>> list(lst)
    [1, 2]
    >>> sum(lst)
    3

    # cl4py also supports dotted and circular lists.
    >>> lisp.eval( ('CONS', 1, ('CONS', 2, 3 )) )
    DottedList(1, 2, 3)

    >>> twos = cl.cons(2,2)
    >>> twos.cdr = twos
    >>> twos
    DottedList(2, ...)

    >>> cl.mapcar(lisp.function('+'), (1, 2, 3, 4), twos)
    List(3, 4, 5, 6)


Frequently Asked Problems
-------------------------

Why does my Lisp subprocess complain about ``Package QL does not exist``.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, cl4py starts a Lisp subprocess with ``sbcl --script``.  This
means, that the Lisp process will ignore any user initialization files,
including the Quicklisp setup.  However, we provide an extra option for
installing and loading Quicklisp automatically: ``quicklisp=True``


.. code:: python

    >>> lisp = cl4py.Lisp(quicklisp=True);
    >>> ql = lisp.find_package('QL')
    >>> ql.quickload('YOUR-SYSTEM')


Related Projects
----------------

-  `burgled-batteries <https://github.com/pinterface/burgled-batteries>`_
   - A bridge between Python and Lisp. The goal is that Lisp programs can
   use Python libraries, which is in some sense the opposite of
   cl4py. Furthermore it relies on the less portable mechanism of FFI
   calls.
-  `CLAUDE <https://www.nicklevine.org/claude/>`_
   - An earlier attempt to access Lisp libraries from Python. The key
   difference is that cl4py does not run Lisp directly in the host
   process. This makes cl4py more portable, but complicates the exchange of
   data.
-  `cl-python <https://github.com/metawilm/cl-python>`_
   - A much heavier solution than cl4py --- let's simply implement Python
   in Lisp! An amazing project. However, cl-python cannot access foreign
   libraries, e.g., NumPy. And people are probably hesitant to migrate away
   from CPython.
-  `Hy <http://docs.hylang.org/en/stable/>`_
   - Python, but with Lisp syntax. This project is certainly a great way to
   get started with Lisp. It allows you to study the advantages of Lisp's
   seemingly weird syntax, without leaving the comfortable Python
   ecosystem. Once you understand the advantages of Lisp, you will doubly
   appreciate cl4py for your projects.
-  `py4cl <https://github.com/bendudson/py4cl>`_
   - A library that allows Common Lisp code to access Python libraries.  It
   is basically the inverse of cl4py.
