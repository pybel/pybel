Technology
==========
This page is meant to describe the development stack for PyBEL, and should be a useful introduction for contributors.

Versioning
----------
PyBEL is versioned on GitHub so changes in its code can be tracked over time and to make use of the variety of
software development plugins. Code is produced following the `Git Flow <https://danielkummer.github.io/git-flow-cheatsheet/>`_
philosophy, which means that new features are coded in branches off of the development branch and merged after they
are triaged. Finally, develop is merged into master for releases. If there are bugs in releases that need to be
fixed quickly, "hot fix" branches from master can be made, then merged back to master and develop after fixing
the problem.

Testing in PyBEL
----------------
PyBEL is written with extensive unit testing and integration testing. Whenever possible, test- driven development is
practiced. This means that new ideas for functions and features are encoded as blank classes/functions and
directly writing tests for the desired output. After tests have been written that define how the code should work,
the implementation can be written.

Test-driven development requires us to think about design before making quick and dirty implementations. This results in
better code. Additionally, thorough testing suites make it possible to catch when changes break existing functionality.

Tests are written with the standard :mod:`unittest` library. Some functionality, such as the :mod:`mock` module, are
only available as default in Python 3, so backports must be used for testing in Python 2

Unit Testing
~~~~~~~~~~~~
Unit tests check that the functionality of the different parts of PyBEL work independently.

An example unit test can be found in :code:`tests.test_parse_bel.TestAbundance.test_short_abundance`. It ensures that
the parser is able to handle a given string describing the abundance of a chemical/other entity in BEL. It tests that
the parser produces the correct output, that the BEL statement is converted to the correct internal representation. In
this example, this is a tuple describing the abundance of oxygen atoms. Finally, it tests that this representation
is added as a node in the underlying BEL graph with the appropriate attributes added.

Integration Testing
~~~~~~~~~~~~~~~~~~~
Integration tests are more high level, and ensure that the software accomplishes more complicated goals by using many
components. An example integration test is found in tests.test_import.TestImport.test_from_fileURL. This test
ensures that a BEL script can be read and results in a NetworkX object that contains all of the information described
in the script

Tox
~~~
While IDEs like PyCharm provide excellent testing tools, they are not programmatic.
`Tox <https://bitbucket.org/hpk42/tox>`_ is python package that provides
a CLI interface to run automated testing procedures (as well as other build functions, that aren't important to explain
here). In PyBEL, it is used to run the unit tests in the :code:`tests` folder with the :mod:`pytest` harness. It also
runs :code:`check-manifest`, builds the documentation with :mod:`sphinx`, and computes the code coverage of the tests.
The entire procedure is defined in :code:`tox.ini`. Tox also allows test to be done on many different versions of
Python.

Continuous Integration
~~~~~~~~~~~~~~~~~~~~~~
Continuous integration is a philosophy of automatically testing code as it changes. PyBEL makes use of the Travis CI
server to perform testing because of its tight integration with GitHub. Travis automatically installs git hooks
inside GitHub so it knows when a new commit is made. Upon each commit, Travis downloads the newest commit from GitHub
and runs the tests configured in the :code:`.travis.yml` file in the top level of the PyBEL repository. This file
effectively instructs the Travis CI server to run Tox. It also allows for the modification of the environment variables.
This is used in PyBEL to test many different versions of python.

Code Coverage
~~~~~~~~~~~~~
After building, Travis sends code coverage results to `codecov.io <https://codecov.io/gh/pybel/pybel>`_. This site helps
visualize untested code and track the improvement of testing coverage over time. It also integrates with GitHub to show
which feature branches are inadequately tested. In development of PyBEL, inadequately tested code is not allowed to be
merged into develop.

Versioning
~~~~~~~~~~
PyBEL uses semantic versioning. In general, the project's version string will has a suffix :code:`-dev` like in
:code:`0.3.4-dev` throughout the development cycle. After code is merged from feature branches to develop and it is
time to deploy, this suffix is removed and develop branch is merged into master.

The version string appears in multiple places throughout the project, so BumpVersion is used to automate the updating
of these version strings. See .bumpversion.cfg for more information.

Deployment
----------
PyBEL is also distributed through PyPI (pronounced Py-Pee-Eye).
Travis CI has a wonderful integration with PyPI, so any time a tag is made on the master branch (and also assuming the
tests pass), a new distribution is packed and sent to PyPI. Refer to the "deploy" section at the bottom of the
:code:`.travis.yml` file for more information, or the Travis CI `PyPI deployment documentation <https://docs.travis-ci.com/user/deployment/pypi/>`_.
As a side note, Travis CI has an encryption tool so the password for the PyPI account can be displayed publicly
on GitHub. Travis decrypts it before performing the upload to PyPI.

Steps
~~~~~
1. :code:`bumpversion release` on development branch
2. Push to git
3. After tests pass, merge develop in to master
4. After tests pass, create a tag on GitHub with the same name as the version number (on master)
5. Travis will automatically deploy to PyPI after tests pass. After checking deployment has been successful,
   switch to develop and :code:`bumpversion patch`
