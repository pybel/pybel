PyBEL |release| Documentation
=============================
Biological Expression Language (BEL) is a domain-specific language that enables the expression of complex molecular
relationships and their context in a machine-readable form. Its simple grammar and expressive power have led to its
successful use in the to describe complex disease networks with several thousands of relationships.

PyBEL is a pure Python software package that parses BEL documents, validates their semantics, and facilitates data
interchange between common formats and database systems like JSON, CSV, Excel, SQL, CX, and Neo4J. Its companion
package, `PyBEL-Tools <http://pybel-tools.readthedocs.io/>`_, contains a library of functions for analysis of
biological networks. For result-oriented guides, see the `PyBEL-Notebooks <https://github.com/pybel/pybel-notebooks>`_
repository.

Installation is as easy as getting the code from `PyPI <https://pypi.python.org/pypi/pybel>`_ with
:code:`python3 -m pip install pybel`. See the :doc:`installation <introduction/installation>` documentation.

For citation information, see the :doc:`references <meta/references>` page.

PyBEL is tested on Python 3.5+ on Mac OS and Linux using
`Travis CI <https://travis-ci.org/pybel/pybel>`_ as well as on Windows using
`AppVeyor <https://ci.appveyor.com/project/cthoyt/pybel>`_.

.. seealso::

    - Specified by `BEL 1.0 <https://github.com/OpenBEL/language/raw/master/docs/version_1.0/bel_specification_version_1.0.pdf>`_,
      `BEL 2.0 <https://github.com/OpenBEL/language/raw/master/docs/version_2.0/bel_specification_version_2.0.pdf>`_, and
      `BEL 2.0+ <https://biological-expression-language.github.io>`_
    - Documented on `Read the Docs <http://pybel.readthedocs.io/>`_
    - Versioned on `GitHub <https://github.com/pybel/pybel>`_
    - Tested on `Travis CI <https://travis-ci.org/pybel/pybel>`_
    - Distributed by `PyPI <https://pypi.python.org/pypi/pybel>`_

.. toctree::
   :maxdepth: 2
   :caption: Getting Started
   :name: start

   introduction/overview
   introduction/installation

.. toctree::
   :maxdepth: 2
   :caption: Data Structure
   :name: data

   reference/struct/datamodel
   reference/struct/examples
   reference/struct/filters
   reference/struct/grouping
   reference/struct/operators
   reference/struct/pipeline
   reference/struct/query
   reference/struct/summary

.. toctree::
   :maxdepth: 2
   :caption: Mutations
   :name: mutations

   reference/mutations/mutations
   reference/mutations/collapse
   reference/mutations/deletion
   reference/mutations/expansion
   reference/mutations/induction
   reference/mutations/induction_expansion
   reference/mutations/inference
   reference/mutations/metadata

.. toctree::
   :maxdepth: 2
   :caption: Conversion
   :name: conversion

   reference/io

.. toctree::
   :caption: Database
   :name: database

   reference/database/manager
   reference/database/models

.. toctree::
   :maxdepth: 2
   :caption: Topic Guide
   :name: topics

   topics/cookbook
   topics/cli

.. toctree::
   :caption: Reference
   :name: reference

   reference/constants
   reference/parser
   reference/dsl
   reference/logging

.. toctree::
   :caption: Project
   :name: project

   meta/references
   meta/postmortem
   meta/technology

Indices and Tables
------------------
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
