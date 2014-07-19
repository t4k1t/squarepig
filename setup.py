#!/usr/bin/python3

""" Setup script for Square Pig. """

from setuptools import setup
from textwrap import dedent
import os

here = os.path.abspath(os.path.dirname(__file__))


def get_version(fname='squarepig/__init__.py'):
    """Fetch version from file."""
    with open(fname) as f:
        for line in f:
            if line.startswith('__version__'):
                return eval(line.split('=')[-1])


setup(
    name="squarepig",
    version=get_version(),
    license='GPLv3',

    description="A playlist mangler",
    long_description=dedent("""
        Square Pig takes files from a playlist and copies those files to a
        target folder in the order they are listed in the playlist
        and prepends the filenames with consecutive numbers."""),

    url='https://github.com/tablet-mode/squarepig',

    author='Tablet Mode',
    author_email='tablet-mode@monochromatic.cc',

        keywords='playlist audio',

    packages=['squarepig'],
    install_requires=[],

    entry_points={
        'console_scripts': ['squarepig = squarepig.main:main', ]
    },

    classifiers=[
        'Development Status :: 5 - Production/Stable',

        'License :: OSI Approved :: GPLv3 License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)
