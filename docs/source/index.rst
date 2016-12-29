PyBEL Documentation
===================

Biological Expression Language (BEL) is a domain specific language that enables the expression of complex molecular
relationships and their context in a machine-readable form. Its simple grammar and expressive power have led to its
successful use in the IMI project, AETIONOMY, to describe complex disease networks with several thousands of
relationships.

PyBEL is a Python software package that parses BEL statements, validates their semantics, applies common graph
algorithms, and allows for data interchange with common formats like Neo4J, JSON, CSV, Excel, and SQL.

PyBEL provides a simple API so bioinformaticians and scientists with limited programming knowledge can easily use it
to interface with BEL graphs, but is built on a rich framework that can be extended to develop new algorithms.

Installation is as easy as getting the code from PyPI with :code:`pip install pybel`

.. toctree::
   :maxdepth: 2

   installation
   overview
   cookbook
   reference
   logging
   roadmap

Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
