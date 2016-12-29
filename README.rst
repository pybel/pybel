PyBEL
=====

:code:`PyBEL` is a Python software package that parses BEL statements, validates their semantics, applies common graph
algorithms, and allows for data interchange between common formats and database systems like JSON, CSV, SQL, and Neo4J.

Development:

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

.. |python_versions| image::  https://img.shields.io/pypi/pyversions/PyBEL.svg
    :alt: Stable Supported Python Versions
	
.. |pypi_version| image:: https://img.shields.io/pypi/v/PyBEL.svg

.. |pypi_license| image:: https://img.shields.io/pypi/l/PyBEL.svg
	

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

This example retrieves a BEL file from a path and exports to a GraphML file for use in Cytoscape.

.. code-block:: sh

    $ pybel convert --path ~/Desktop/example.bel --graphml ~/Desktop/example.graphml
   
In Cytoscape, open with :code:`Import > Network > From File`.

Export to Neo4j
~~~~~~~~~~~~~~~

This example retrieves a BEL file from a URL, and exports to Neo4j

.. code-block:: sh

   $ URL="http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel"
   $ NEO="neo4j:neo4j@localhost:7474"
   $
   $ pybel convert --url $URL --neo $NEO

Multiple Export
~~~~~~~~~~~~~~~

This example gets a file from stdin and exports to multiple locations, with logging

.. code-block:: sh

   $ URL="http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel"
   $ NEO="neo4j:neo4j@localhost:7474"
   $
   $ curl $URL | pybel convert --neo $NEO --json ~/Desktop/example.json --log-file ~/Desktop/log.txt

Installation
------------

|pypi_version| |python_versions| |pypi_license|


PyBEL can be installed easily from `PyPI <https://pypi.python.org/pypi/pybel>`_ with the following code in
your favorite terminal:

.. code-block:: sh

   pip install pybel

See the `documentation <http://pybel.readthedocs.io/>`_ for more advanced instructions.

Contributing
------------

Contributions, whether filing an issue, making a pull request, or forking, are appreciated. See
:code:`CONTRIBUTING.rst` for more information on getting involved.

Acknowledgements
----------------

- This software is proudly built with Paul McGuire's PyParsing package.
- Scott Colby designed our logo and provided sage advice
- Core Team: Charles Tapley Hoyt, Andrej Konotopez, Christian Ebeling

Find Us
-------

- `Read the Docs <http://pybel.readthedocs.io/>`_
- `GitHub <https://github.com/pybel/pybel>`_
- `PyPI <https://pypi.python.org/pypi/pybel>`_
- `Chat on Gitter <https://gitter.im/pybel/Lobby>`_
