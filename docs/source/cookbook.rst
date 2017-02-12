Cookbook
========
PyBEL has a programmatic API for analysis using the swath of tools provided by PyBEL, NetworkX, and the community of
python programmers in Network Science. The most useful functions for users are exposed at the top level package.
These functions allow for easy import from URL, file, iterable, or a database. It also includes various export options.

Draw NetworkX and MatplotLib
----------------------------

.. code-block:: python

   >>> import pybel, networkx
   >>> url = 'http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel'
   >>> g = pybel.from_url(url)  # takes about 20 seconds
   >>> networkx.draw(g)

Export to Neo4j
---------------

.. code-block:: python

   >>> import pybel, py2neo
   >>> url = 'http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel'
   >>> g = pybel.from_url(url)
   >>> neo_graph = py2neo.Graph("http://localhost:7474/db/data/")  # use your own connection settings
   >>> pybel.to_neo4j(g, neo_graph)
