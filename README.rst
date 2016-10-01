PyBEL
=====

.. image:: https://travis-ci.com/cthoyt/pybel.svg?token=2tyMYiCcZbjqYscNWXwZ&branch=master
    :target: https://travis-ci.com/cthoyt/pybel

Biological Expression Language (BEL) is a domain specific language that enables the expression of complex molecular relationships and their context in a machine-readable form. Its simple grammar and expressive power have led to its successful use in the IMI project, AETIONOMY, to describe complex disease networks with several thousands of relationships.

PyBEL is a Python software package that parses the BEL syntax, validates its semantics with the contained namespaces, applies common graph algorithms, and allows for data interchange with common formats like Neo4J, CSV, Excel, and MySQL.
PyBEL provides a simple API so bioinformaticians and scientists with limited programming knowledge can easily use it to interface with BEL graphs, but is built on a rich framework that can be extended to develop new algorithms.

.. code-block:: python

   >>> import pybel, networkx
   >>> g = pybel.from_url('http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel')
   >>> networkx.draw(g)

Command Line Interface
----------------------

PyBEL also installs a command line interface with the command :code:`pybel` for simple utilities such as data conversion.

.. code-block:: sh

   $ URL="http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel"
   $ NEO="neo4j:neo4j@localhost:7474"
   $
   $ pybel to_neo --url "$URL" --neo "$NEO"


Installation
------------

In the future, this repository will be open to the public for use. Installation will be as easy as:

.. code-block:: sh

   pip install pybel
	

Contributing
------------

Contributions, whether filing an issue, making a pull request, or forking, are appreciated. See :code:`CONTRIBUTING.rst` for more information on getting involved.
