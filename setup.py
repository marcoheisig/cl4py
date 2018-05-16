"""The cl4py setup.

See:
https://github.com/marcoheisig/cl4py
"""

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.org'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='cl4py',
    version='1.0.0',
    description='Common Lisp for Python',
    license='MIT',
    url='https://github.com/marcoheisig/cl4py',
    author='Marco Heisig',
    author_email='marco.heisig@fau.de',
    packages=find_packages(exclude=['contrib', 'docs', 'test']),
    install_requires=[],
    extras_require={},
    python_requires='>=3.5',
    long_description=long_description,

    # content_type is actually org-mode, but setup.py is quite
    # restrictive in this respect...
    long_description_content_type='text/plain',
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

    project_urls={
        'Bug Reports': 'https://github.com/marcoheisig/cl4py/issues',
        'Source': 'https://github.com/marcoheisig/cl4py',
    },
)
