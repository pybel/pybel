PyBEL
=====

:code:`pybel` is a Python software package that parses BEL scripts, validates their semantics, and facilitates data
interchange between common formats and database systems like JSON, CSV, Excel, SQL, CX, and Neo4J. Its companion
package, `pybel_tools <http://pybel-tools.readthedocs.io/>`_, contains a library of functions for analysis of
biological networks.

=========== =============== ================== =======================
Stable      |stable_build|  |stable_coverage|  |stable_documentation| 
Development |develop_build| |develop_coverage| |develop_documentation|
=========== =============== ================== =======================


.. |stable_build| image:: https://travis-ci.org/pybel/pybel.svg?branch=master
    :target: https://travis-ci.org/pybel/pybel
    :alt: Stable Build Status

.. |stable_coverage| image:: https://codecov.io/gh/pybel/pybel/coverage.svg?branch=master
    :target: https://codecov.io/gh/pybel/pybel?branch=master
    :alt: Stable Coverage Status

.. |stable_documentation| image:: https://readthedocs.org/projects/pybel/badge/?version=stable
    :target: http://pybel.readthedocs.io/en/stable/
    :alt: Stable Documentation Status

.. |develop_build| image:: https://travis-ci.org/pybel/pybel.svg?branch=develop
    :target: https://travis-ci.org/pybel/pybel
    :alt: Development Build Status

.. |develop_coverage| image:: https://codecov.io/gh/pybel/pybel/coverage.svg?branch=develop
    :target: https://codecov.io/gh/pybel/pybel?branch=develop
    :alt: Development Coverage Status

.. |develop_documentation| image:: https://readthedocs.org/projects/pybel/badge/?version=latest
    :target: http://pybel.readthedocs.io/en/latest/
    :alt: Development Documentation Status

.. |climate| image:: https://codeclimate.com/github/pybel/pybel/badges/gpa.svg
    :target: https://codeclimate.com/github/pybel/pybel
    :alt: Code Climate

.. |python_versions| image:: https://img.shields.io/pypi/pyversions/PyBEL.svg
    :alt: Stable Supported Python Versions
	
.. |pypi_version| image:: https://img.shields.io/pypi/v/PyBEL.svg
    :alt: Current version on PyPI

.. |pypi_license| image:: https://img.shields.io/pypi/l/PyBEL.svg
    :alt: Apache 2.0 License


Biological Expression Language (BEL) is a domain-specific language that enables the expression of complex molecular
relationships and their context in a machine-readable form. Its simple grammar and expressive power have led to its
successful use in the `IMI <https://www.imi.europa.eu/>`_ project, `AETIONOMY <http://www.aetionomy.eu/>`_, to describe
complex disease networks with several thousands of relationships.

:code:`pybel` provides a simple API so bioinformaticians and scientists with limited programming knowledge can easily
use it to interface with BEL graphs, but is built on a rich framework that can be extended to develop new algorithms.

.. code-block:: python

   >>> import pybel, networkx
   >>> g = pybel.from_url('http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel')
   >>> networkx.draw(g)  # NOTE: requires matplotlib as a dependency, which isn't automatically installed

PyBEL also installs a command line interface with the command :code:`pybel` for simple utilities such as data
conversion. Need help? All logs go to :code:`~/.pybel` or add :code:`-v` for verbose output to the standard error
stream. In this example, a BEL file is exported to GraphML for viewing in Cytoscape.

.. code-block:: sh

    $ pybel convert --path ~/Desktop/example.bel --graphml ~/Desktop/example.graphml
   
In Cytoscape, open with :code:`Import > Network > From File`.


Installation
------------

|pypi_version| |python_versions| |pypi_license|


PyBEL can be installed easily from `PyPI <https://pypi.python.org/pypi/pybel>`_ with the following code in
your favorite terminal:

.. code-block:: sh

   python3 -m pip install pybel

See the `installation documentation <http://pybel.readthedocs.io/en/latest/installation.html>`_ for more advanced
instructions. Also, check the change log at :code:`CHANGELOG.rst`.

Contributing
------------

Contributions, whether filing an issue, making a pull request, or forking, are appreciated. See
:code:`CONTRIBUTING.rst` for more information on getting involved. Please add your name to :code:`AUTHORS.rst`!

Acknowledgements
----------------

- This software is proudly built with Paul McGuire's `PyParsing <http://pyparsing.wikispaces.com/>`_ package.
- `Scott Colby <https://github.com/scolby33>`_ designed our `logo <https://github.com/pybel/pybel-art>`_ and provided sage advice
- `Christian Ebeling <https://github.com/cebel>`_ for supervision and consultation

Links
-----

- Specified by `BEL 1.0 <http://openbel.org/language/web/version_1.0/bel_specification_version_1.0.html>`_ and
  `BEL 2.0 <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html>`_
- Documented on `Read the Docs <http://pybel.readthedocs.io/>`_
- Versioned on `GitHub <https://github.com/pybel/pybel>`_
- Tested on `Travis CI <https://travis-ci.org/pybel/pybel>`_
- Distributed by `PyPI <https://pypi.python.org/pypi/pybel>`_
- Chat on `Gitter <https://gitter.im/pybel/Lobby>`_
