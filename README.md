travis-solo
===========

*travis-solo* is local Travis build runner. *travis-solo* is itself written in Python and works with:

* CPython 2.6, 2.7, 3.2, 3.3
* PyPy 1.9

Supported operating systems:

* GNU/Linux
* OS X

Usage
-----

Execute *travis-solo* in directory containing ``.travis.yml`` configuration file. It's return code will be 0 in case of success and non-zero in case of failure.


Restrictions
------------

First of all you need to remember that your local environment is probably very different than Travis' so all those ``apt-get`` calls may not work as intended.

* The only type of project supported right now is Python.
* Supported configuration properties:
	* ``before_install``
	* ``install``
 * ``before_script``
 * ``script``
 * ``after_script``
 * ``python``
	* ``matrix``
 * ``env``
* ``travis-solo`` sets the following environmental variables:
 * ``TRAVIS=true``
 * ``CI=true``
 * ``TRAVIS_SOLO=true``
 * ``TRAVIS_PYTHON_VERSION=...`` depending on configuration
* Commands involving ``sudo`` word are silently discarded at the moment

Copyright
---------

Copyright (C) 2013 Jakub Stasiak

This source code is licensed under MIT license, see LICENSE file for details.
