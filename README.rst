cl4py - Common Lisp for Python
==============================

The library cl4py (pronounce as *clappy*) allows Python programs to call
Common Lisp libraries.

Motivation
----------

You are a Python programmer, but you want access to some of the powerful
features of Lisp, for example to compile code at run time?  Or you want to
use some `awesome Lisp libraries <http://codys.club/awesome-cl/>`__?  Or
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

    >>> lisp.eval( ('+', 2, 3) )
    5

    >>> add = lisp.function('+')
    >>> add(1, 2, 3, 4)
    10

    >>> div = lisp.function('/')
    >>> div(2, 4)
    Fraction(1, 2)

Some Lisp data structures have no direct equivalent in Python, most
notably, cons cells.  The cl4py module provides a suitable Cons class and
converts List conses to instances of cl4py.Cons.

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

It soon becomes clumsy to look up individual Lisp functions by name.
Instead, it is usually better to convert entire Lisp packages to Python
modules, like this:

.. code:: python

    >>> cl = lisp.function('find-package')('CL')
    >>> cl.oppd(5)
    True

    >>> cl.cons(5, None)
    List(5)

    >>> cl.remove(5, [1, 5, 2, 7, 5, 9])
    [1, 2, 3, 4]

    # Higher-order functions work, too!
    >>> cl.mapcar(cl.constantly(4), (1, 2, 3))
    List(4, 4, 4)

    # Of course, circular objects of all kinds are supported.
    >>> twos = cl.cons(2,2)
    >>> twos.cdr = twos
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

    >>> lisp = cl4py.Lisp(quicklisp=True); cl = lisp.function('find-package')('CL')
    >>> ql = cl.find_package('QL')
    >>> ql.quickload('YOUR-SYSTEM')


Related Projects
----------------

-  `burgled-batteries <https://github.com/pinterface/burgled-batteries>`__
   - A bridge between Python and Lisp. The goal is that Lisp programs can
   use Python libraries, which is in some sense the opposite of
   cl4py. Furthermore it relies on the less portable mechanism of FFI
   calls.
-  `CLAUDE <https://www.nicklevine.org/claude/>`__
   - An earlier attempt to access Lisp libraries from Python. The key
   difference is that cl4py does not run Lisp directly in the host
   process. This makes cl4py more portable, but complicates the exchange of
   data.
-  `cl-python <https://github.com/metawilm/cl-python>`__
   - A much heavier solution than cl4py --- let's simply implement Python
   in Lisp! An amazing project. However, cl-python cannot access foreign
   libraries, e.g., NumPy. And people are probably hesitant to migrate away
   from CPython.
-  `Hy <http://docs.hylang.org/en/stable/>`__
   - Python, but with Lisp syntax. This project is certainly a great way to
   get started with Lisp. It allows you to study the advantages of Lisp's
   seemingly weird syntax, without leaving the comfortable Python
   ecosystem. Once you understand the advantages of Lisp, you will doubly
   appreciate cl4py for your projects.
-  `py4cl <https://github.com/bendudson/py4cl>`__
   - A library that allows Common Lisp code to access Python libraries.  It
   is basically the inverse of cl4py.
