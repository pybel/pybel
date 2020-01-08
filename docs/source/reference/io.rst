Input and Output
================
.. automodule:: pybel.io

Import
------
Parsing Modes
~~~~~~~~~~~~~
The PyBEL parser has several modes that can be enabled and disabled. They are described below.

Allow Naked Names
*****************
By default, this is set to :code:`False`. The parser does not allow identifiers that are not qualified with
namespaces (*naked names*), like in :code:`p(YFG)`. A proper namespace, like :code:`p(HGNC:YFG)` must be used. By
setting this to :code:`True`, the parser becomes permissive to naked names. In general, this is bad practice and this
feature will be removed in the future.

Allow Nested
************
By default, this is set to :code:`False`. The parser does not allow nested statements is disabled. See `overview`.
By setting this to :code:`True` the parser will accept nested statements one level deep.

Citation Clearing
*****************
By default, this is set to :code:`True`. While the BEL specification clearly states how the language should be used as
a state machine, many BEL documents do not conform to the strict :code:`SET`/:code:`UNSET` rules. To guard against
annotations accidentally carried from one set of statements to the next, the parser has two modes. By default, in
citation clearing mode, when a :code:`SET CITATION` command is reached, it will clear all other annotations (except
the :code:`STATEMENT_GROUP`, which has higher priority). This behavior can be disabled by setting this to :code:`False`
to re-enable strict parsing.

Reference
~~~~~~~~~
.. autofunction:: pybel.from_bel_script
.. autofunction:: pybel.from_bel_script_url
.. autofunction:: pybel.to_bel_script

Transport
---------
All transport pairs are reflective and data-preserving.

Bytes
~~~~~
.. automodule:: pybel.io.gpickle

.. autofunction:: pybel.from_bytes
.. autofunction:: pybel.to_bytes

.. autofunction:: pybel.from_pickle
.. autofunction:: pybel.to_pickle

Node-Link JSON
~~~~~~~~~~~~~~
.. automodule:: pybel.io.nodelink

.. autofunction:: pybel.from_nodelink
.. autofunction:: pybel.to_nodelink

.. autofunction:: pybel.from_nodelink_jsons
.. autofunction:: pybel.to_nodelink_jsons

.. autofunction:: pybel.from_nodelink_file
.. autofunction:: pybel.to_nodelink_file

.. autofunction:: pybel.from_nodelink_gz
.. autofunction:: pybel.to_nodelink_gz

Cyberinfrastructure Exchange
----------------------------
.. automodule:: pybel.io.cx

.. autofunction:: pybel.from_cx
.. autofunction:: pybel.to_cx

.. autofunction:: pybel.from_cx_jsons
.. autofunction:: pybel.to_cx_jsons

.. autofunction:: pybel.from_cx_file
.. autofunction:: pybel.to_cx_file

.. autofunction:: pybel.from_cx_gz
.. autofunction:: pybel.to_cx_gz

JSON Graph Interchange Format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. automodule:: pybel.io.jgif

.. autofunction:: pybel.from_jgif
.. autofunction:: pybel.to_jgif

.. autofunction:: pybel.from_jgif_jsons
.. autofunction:: pybel.to_jgif_jsons

.. autofunction:: pybel.from_jgif_file
.. autofunction:: pybel.to_jgif_file

.. autofunction:: pybel.from_jgif_gz
.. autofunction:: pybel.to_jgif_gz

.. autofunction:: pybel.post_jgif

.. autofunction:: pybel.from_cbn_jgif

Export
------
Umbrella Node-Link JSON
~~~~~~~~~~~~~~~~~~~~~~~
.. automodule:: pybel.io.umbrella_nodelink

.. autofunction:: pybel.to_umbrella_nodelink
.. autofunction:: pybel.to_umbrella_nodelink_file

GraphML
~~~~~~~
.. automodule:: pybel.io.graphml

.. autofunction:: pybel.to_graphml

Miscellaneous
~~~~~~~~~~~~~
.. automodule:: pybel.io.extras

.. autofunction:: pybel.to_csv
.. autofunction:: pybel.to_sif
.. autofunction:: pybel.to_gsea
.. autofunction:: pybel.to_tsv

Databases
---------
SQL Databases
~~~~~~~~~~~~~
.. automodule:: pybel.manager.database_io

.. autofunction:: pybel.from_database
.. autofunction:: pybel.to_database

Neo4j
~~~~~
.. automodule:: pybel.io.neo4j

.. autofunction:: pybel.to_neo4j

BEL Commons
-----------
.. automodule:: pybel.io.web

.. autofunction:: pybel.from_web
.. autofunction:: pybel.to_web

INDRA
-----
.. automodule:: pybel.io.indra

.. autofunction:: pybel.from_indra_statements
.. autofunction:: pybel.to_indra_statements

.. autofunction:: pybel.from_biopax
