PyBEL Documentation
===================

Biological Expression Language (BEL) is a domain-specific language that enables the expression of complex molecular
relationships and their context in a machine-readable form. Its simple grammar and expressive power have led to its
successful use in the `IMI <https://www.imi.europa.eu/>`_ project, `AETIONOMY <http://www.aetionomy.eu/>`_, to describe
complex disease networks with several thousands of relationships.

:code:`pybel` is a Python software package that parses BEL scripts, validates their semantics, and facilitates data
interchange between common formats and database systems like JSON, CSV, Excel, SQL, CX, and Neo4J. Its companion
package, `pybel_tools <http://pybel-tools.readthedocs.io/>`_, contains a library of functions for analysis of
biological networks.

:code:`pybel` provides a simple API so bioinformaticians and scientists with limited programming knowledge can easily
use it to interface with BEL graphs, but is built on a rich framework that can be extended to develop new algorithms.

Installation is as easy as getting the code from PyPI with :code:`python3 -m pip install pybel`

.. toctree::
   :maxdepth: 2

   installation
   overview
   datamodel
   io
   cookbook
   commandline
   troubleshooting
   logging

.. toctree::
   :caption: Reference
   :name: reference

   constants
   parser
   manager
   utilities

.. toctree::
   :caption: Project
   :name: project

   roadmap
   technology


Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
