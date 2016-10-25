PyBEL
=====

:code:`PyBEL` is a Python software package that parses BEL statements, validates their semantics, applies common graph
algorithms, and allows for data interchange between common formats like Neo4J, JSON, CSV, Excel, and SQL.

=========== =============== ================== ======================= ====================
Stable      |stable_build|  |stable_coverage|  |stable_documentation|  |stable_pyversions|
Development |develop_build| |develop_coverage| |develop_documentation| |develop_pyversions|
=========== =============== ================== ======================= ====================


.. |stable_build| image:: https://travis-ci.org/pybel/pybel.svg?branch=master
    :target: https://travis-ci.org/pybel/pybel
    :alt: Stable Build Status

.. |stable_coverage| image:: https://codecov.io/gh/pybel/pybel/coverage.svg?branch=master
    :target: https://codecov.io/gh/pybel/pybel?branch=master
    :alt: Stable Coverage Status

.. |stable_documentation| image:: https://readthedocs.org/projects/pybel/badge/?version=stable
    :target: http://pybel.readthedocs.io/en/stable/
    :alt: Stable Documentation Status

.. |stable_pyversions| image:: https://img.shields.io/badge/python-2.7%2C%203.5-blue.svg
    :alt: Stable Supported Python Versions

.. |develop_build| image:: https://travis-ci.org/pybel/pybel.svg?branch=develop
    :target: https://travis-ci.org/pybel/pybel
    :alt: Development Build Status

.. |develop_coverage| image:: https://codecov.io/gh/pybel/pybel/coverage.svg?branch=develop
    :target: https://codecov.io/gh/pybel/pybel?branch=develop
    :alt: Development Coverage Status

.. |develop_documentation| image:: https://readthedocs.org/projects/pybel/badge/?version=latest
    :target: http://pybel.readthedocs.io/en/latest/
    :alt: Development Documentation Status

.. |develop_pyversions| image:: https://img.shields.io/badge/python-2.7%2C%203.5-blue.svg
    :alt: Development Supported Python Versions

.. |climate| image:: https://codeclimate.com/github/pybel/pybel/badges/gpa.svg
    :target: https://codeclimate.com/github/pybel/pybel
    :alt: Code Climate


Biological Expression Language (BEL) is a domain specific language that enables the expression of complex molecular
relationships and their context in a machine-readable form. Its simple grammar and expressive power have led to its
successful use in the `IMI <https://www.imi.europa.eu/>`_ project, `AETIONOMY <http://www.aetionomy.eu/>`_, to describe
complex disease networks with several thousands of relationships.

PyBEL provides a simple API so bioinformaticians and scientists with limited programming knowledge can easily use it to
interface with BEL graphs, but is built on a rich framework that can be extended to develop new algorithms.

.. code-block:: python

   >>> import pybel, networkx
   >>> g = pybel.from_url('http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel')
   >>> networkx.draw(g)

Command Line Interface
----------------------

PyBEL also installs a command line interface with the command :code:`pybel` for simple utilities such as data
conversion. Need help? All logs go to :code:`~/.pybel` or add :code:`-v` for verbose output to the standard error
stream

Export for Cytoscape
~~~~~~~~~~~~~~~~~~~~

.. code-block:: sh

    $ pybel convert --path ~/Desktop/example.bel --graphml ~/Desktop/example.graphml
   
In Cytoscape, open with :code:`Import > Network > From File`.

Export to Neo4j
~~~~~~~~~~~~~~~

.. code-block:: sh

   $ URL="http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel"
   $ NEO="neo4j:neo4j@localhost:7474"
   $
   $ pybel to_neo --url $URL --neo $NEO


Installation
------------

Installation is as easy as running from your favorite terminal:

.. code-block:: sh

   pip install pybel

Currently, :code:`PyBEL` officially supports Python 2.7 and Python 3.5. Builds also pass on Python 3.4, and there
are some problems that can be solved with the installation of :code:`pandas` for Python 3.3 usage.

Contributing
------------

Contributions, whether filing an issue, making a pull request, or forking, are appreciated. See
:code:`CONTRIBUTING.rst` for more information on getting involved.

Acknowledgements
----------------

- PyBEL is proudly built with Paul McGuire's PyParsing package.
- Scott Colby designed our logo and provided sage advice
- PyBEL Core Team: Charles Tapley Hoyt, Andrej Konotopez, Christian Ebeling

Find Us
-------

- http://pybel.readthedocs.io/
- https://github.com/pybel/pybel
- https://pypi.python.org/pypi/pybel
