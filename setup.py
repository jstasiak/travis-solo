#!/usr/bin/env python
# -*- coding: utf-8 -*
from __future__ import absolute_import, division, print_function

import platform

from setuptools import setup

from os import environ, getcwd
from os.path import abspath, dirname, join

PROJECT_ROOT = abspath(dirname(__file__))
with open(join(PROJECT_ROOT, 'README.md')) as f:
	readme = f.read()

with open(join(PROJECT_ROOT, 'travis_solo.py')) as f:
	version_line = [line for line in f.readlines() if line.startswith('__version__')][0]
	version = version_line.split('=')[1].strip().strip("'")

setup(
	name='travis-solo',
	version=version,
	description='Local Travis build runner',
	long_description=readme,
	author='Jakub Stasiak',
	author_email='jakub@stasiak.at',
	py_modules=['travis_solo'],
	platforms=['unix', 'linux', 'osx'],
	license='http://opensource.org/licenses/MIT',
	install_requires=[
		'PyYAML',
		'termcolor',
	],
	tests_requre=[
		'nose==1.2.1',
	],
	entry_points=dict(
		console_scripts=[
			'travis-solo = travis_solo:main',
		],
	),
	classifiers=[
		'Development Status :: 3 - Alpha',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: MIT License',
		'Operating System :: POSIX',
		'Operating System :: POSIX :: Linux',
		'Operating System :: MacOS :: MacOS X',
		'Topic :: Software Development :: Testing',
		'Topic :: Software Development :: Libraries',
		'Topic :: Utilities',
		'Programming Language :: Python',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.6',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.2',
		'Programming Language :: Python :: 3.3',
		'Programming Language :: Python :: Implementation :: CPython',
		'Programming Language :: Python :: Implementation :: PyPy',
	],
)