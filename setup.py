"""The cl4py setup.

See:
https://github.com/marcoheisig/cl4py
"""

from setuptools import setup, find_packages
from codecs import open
from os import path

setup(
    name='cl4py',
    version='1.0.1',
    description='Common Lisp for Python',
    license='MIT',
    url='https://github.com/marcoheisig/cl4py',
    author='Marco Heisig',
    author_email='marco.heisig@fau.de',
    packages=find_packages(exclude=['contrib', 'docs', 'test']),
    install_requires=[],
    extras_require={},
    long_description=long_description,
    keywords='foreign functions FFI',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Lisp' ,
    ],

    package_data={
        'cl4py': ['cl4py/py.lisp'],
    },
)
