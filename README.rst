travis-solo
===========

.. image:: https://travis-ci.org/jstasiak/travis-solo.png?branch=master
   :alt: Build status
   :target: https://travis-ci.org/jstasiak/travis-solo

*travis-solo* is local Travis build runner. *travis-solo* is itself written in Python and works with:

* CPython 2.6, 2.7, 3.2, 3.3
* PyPy 1.9

Supported operating systems:

* GNU/Linux
* OS X

Usage
-----

Execute *travis-solo* in directory containing ``.travis.yml`` configuration file. It's return code will be 0 in case of success and non-zero in case of failure.

``travis-solo -h`` or ``travis-solo --help`` will display usage information.

Example ``.travis.yml`` file::

    language: python
    python:
        - "2.7"
    install:
        - sudo this won't be executed anyway
    env:
        - VAR=foo
        - VAR=bar
    matrix:
        include:
          - python: "2.7"
            env: VAR=baz

    script: echo "VAR is $VAR"

Output::

    -> % travis-solo 


    Build configuration python2.7 (VAR=u'foo') running
    Preparing the environment
    $ virtualenv --distribute --python=python2.7 /Users/aa/projects/travis-solo/.travis-solo/2.7
    Running virtualenv with interpreter /usr/local/bin/python2.7
    New python executable in /Users/aa/projects/travis-solo/.travis-solo/2.7/bin/python
    Installing distribute...........................................................................................................................................................................................................................done.
    Installing pip................done.
    "sudo this won't be executed anyway" ignored because it contains sudo reference
    $ echo "VAR is $VAR"
    VAR is foo


    Build configuration python2.7 (VAR=u'bar') running
    Preparing the environment
    "sudo this won't be executed anyway" ignored because it contains sudo reference
    $ echo "VAR is $VAR"
    VAR is bar


    Build configuration python2.7 (VAR=u'baz') running
    Preparing the environment
    "sudo this won't be executed anyway" ignored because it contains sudo reference
    $ echo "VAR is $VAR"
    VAR is baz


    Build summary:
    python2.7 (VAR=u'foo'): Build succeeded
    python2.7 (VAR=u'bar'): Build succeeded
    python2.7 (VAR=u'baz'): Build succeeded

    -> % echo $?
    0

**travis-solo can of course run tests for itself**.

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
* When running parallel builds (``--jobs X`` where X != 1) you need to make sure that builds don't operate on the same project files at the same time.

  For example: Python package build process can use ``build`` directory to store the results. There is a workaround for that (borrowed from https://github.com/hhatto/autopep8/commit/1c895989422b0a02a32a4383a3f0467b44f20663) - change
  
    python setup.py install # or similar
    
  to
    
    python setup.py build --build-base=".build-$TRAVIS_PYTHON_VERSION" install
    
  This change will make sure that each build environment will operate in separate build directory as far as building your package is concerned.


Copyright
---------

Copyright (C) 2013 Jakub Stasiak

This source code is licensed under MIT license, see LICENSE file for details.
