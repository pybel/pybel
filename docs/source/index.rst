PyBEL Documentation
===================
Biological Expression Language (BEL) is a domain-specific language that enables the expression of complex molecular
relationships and their context in a machine-readable form. Its simple grammar and expressive power have led to its
successful use in the `IMI <https://www.imi.europa.eu/>`_ project, `AETIONOMY <http://www.aetionomy.eu/>`_, to describe
complex disease networks with several thousands of relationships.

PyBEL is a pure Python software package that parses BEL scripts, validates their semantics, and facilitates data
interchange between common formats and database systems like JSON, CSV, Excel, SQL, CX, and Neo4J. Its companion
package, `PyBEL Tools <http://pybel-tools.readthedocs.io/>`_, contains a library of functions for analysis of
biological networks. For result-oriented guides, see the `PyBEL Notebooks <https://github.com/pybel/pybel-notebooks>`_
repository.

Installation is as easy as getting the code from `PyPI <https://pypi.python.org/pypi/pybel>`_ with
:code:`python3 -m pip install pybel`

Citation
--------
If you use PyBEL in your work, please cite [1]_:

.. [1] Hoyt et al., 2017. PyBEL: a computational framework for Biological Expression Language. Bioinformatics, btx660, https://doi.org/10.1093/bioinformatics/btx660

Links
-----
- Specified by `BEL 1.0 <http://openbel.org/language/web/version_1.0/bel_specification_version_1.0.html>`_ and
  `BEL 2.0 <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html>`_
- Documented on `Read the Docs <http://pybel.readthedocs.io/>`_
- Versioned on `GitHub <https://github.com/pybel/pybel>`_
- Tested on `Travis CI <https://travis-ci.org/pybel/pybel>`_
- Distributed by `PyPI <https://pypi.python.org/pypi/pybel>`_
- Chat on `Gitter <https://gitter.im/pybel/Lobby>`_

.. toctree::
   :maxdepth: 2
   :caption: Getting Started
   :name: start

   overview
   installation

.. toctree::
   :maxdepth: 2
   :caption: Data Structure
   :name: data

   datamodel
   examples
   summary
   filters
   mutation

.. toctree::
   :maxdepth: 2
   :caption: Conversion
   :name: conversion

   io

.. toctree::
   :caption: Database
   :name: database

   manager
   models

.. toctree::
   :maxdepth: 2
   :caption: Topic Guide
   :name: topics

   cookbook
   troubleshooting

.. toctree::
   :caption: Reference
   :name: reference

   constants
   parser
   utilities
   dsl
   logging
   extensions

.. toctree::
   :caption: Project
   :name: project

   roadmap
   postmortem
   technology

Indices and Tables
------------------
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
