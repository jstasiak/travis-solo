travis-solo
===========

``travis-solo`` is local Travis build runner for Python projects. ``travis-solo`` is itself written in Python and works on:

* CPython 2.6, 2.7, 3.2, 3.3
* PyPy 1.9

``travis-solo`` works on Linux systems and OS X


Usage
-----

Execute ``travis-solo`` in directory containing ``.travis.yml`` configuration file. It's return code will be 0 in case of success and non-zero in case of failure.


Restrictions
------------

First of all you need to remember that your local environment is probably very different than Travis' so all those ``apt-get`` calls may not work as intended.

* The only type of project supported right now is Python.
* Moreover, the following features of Travis CI aren't supported:

  * ``after_failure`` and ``after_success`` actions - they're gonna be silently ignored
  * ``TRAVIS_*`` environmental variables - they aren't set by ``travis-solo``

* Commands involving ``sudo`` word are silently discarded at the moment

Copyright
---------

Copyright (C) 2013 Jakub Stasiak

This code is licensed under MIT license, see LICENSE file for details.
