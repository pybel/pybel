PyBEL
===================

Biological Expression Language (BEL) is a domain specific language that enables the expression of complex molecular relationships and their context in a machine-readable form. Its simple grammar and expressive power have led to its successful use in the IMI project, AETIONOMY, to describe complex disease networks with several thousands of relationships.

PyBEL is a Python software package that parses the BEL syntax, validates its semantics with the contained namespaces, applies common graph algorithms, and allows for data interchange with common formats like Neo4J, CSV, Excel, and MySQL. 
PyBEL provides a simple API so bioinformaticians and scientists with limited programming knowledge can easily use it to interface with BEL graphs, but is built on a rich framework that can be extended to develop new algorithms. 


.. code-block:: python
	import pybel
	import networkx

	url = 'http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel'
	g = pybel.parse_from_url(url)

	networkx.draw(g)

Installation
--------------------

Development
~~~~~~~~~~~~~~~~~~~~

For developers, this repository can be cloned and locally installed with pip using the following commands:

.. code-block::
	git clone https://github.com/cthoyt/pybel.git
	cd pybel
	pip install -e .


Usage
~~~~~~~~~~~~~~~~~~~~

In the future, this repository will be open to the public for use. Installation will be as easy as:

.. code:: bash
	pip install pybel
