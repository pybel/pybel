Input and Output
================
.. automodule:: pybel.io

.. autofunction:: pybel.load
.. autofunction:: pybel.dump

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

Hetionet
~~~~~~~~
.. automodule:: pybel.io.hetionet

.. autofunction:: pybel.from_hetionet_json
.. autofunction:: pybel.from_hetionet_file
.. autofunction:: pybel.from_hetionet_gz

.. autofunction:: pybel.get_hetionet

Transport
---------
All transport pairs are reflective and data-preserving.

Bytes
~~~~~
.. automodule:: pybel.io.gpickle

.. autofunction:: pybel.from_bytes
.. autofunction:: pybel.to_bytes

.. autofunction:: pybel.from_bytes_gz
.. autofunction:: pybel.to_bytes_gz

.. autofunction:: pybel.from_pickle
.. autofunction:: pybel.to_pickle

.. autofunction:: pybel.from_pickle_gz
.. autofunction:: pybel.to_pickle_gz

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

Streamable BEL (JSONL)
~~~~~~~~~~~~~~~~~~~~~~
.. automodule:: pybel.io.sbel

.. autofunction:: pybel.from_sbel
.. autofunction:: pybel.to_sbel

.. autofunction:: pybel.from_sbel_file
.. autofunction:: pybel.to_sbel_file

.. autofunction:: pybel.from_sbel_gz
.. autofunction:: pybel.to_sbel_gz

Cyberinfrastructure Exchange
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
.. autofunction:: pybel.from_cbn_jgif_file

GraphDati
~~~~~~~~~
.. automodule:: pybel.io.graphdati

.. autofunction:: pybel.to_graphdati
.. autofunction:: pybel.from_graphdati

.. autofunction:: pybel.to_graphdati_file
.. autofunction:: pybel.from_graphdati_file

.. autofunction:: pybel.to_graphdati_gz
.. autofunction:: pybel.from_graphdati_gz

.. autofunction:: pybel.to_graphdati_jsons
.. autofunction:: pybel.from_graphdati_jsons

.. autofunction:: pybel.to_graphdati_jsonl

.. autofunction:: pybel.to_graphdati_jsonl_gz

INDRA
~~~~~
.. automodule:: pybel.io.indra

.. autofunction:: pybel.from_indra_statements
.. autofunction:: pybel.from_indra_statements_json
.. autofunction:: pybel.from_indra_statements_json_file

.. autofunction:: pybel.to_indra_statements
.. autofunction:: pybel.to_indra_statements_json
.. autofunction:: pybel.to_indra_statements_json_file

.. autofunction:: pybel.from_biopax

Visualization
-------------
Jupyter
~~~~~~~
.. automodule:: pybel.io.jupyter

.. autofunction:: pybel.to_jupyter

Analytical Services
-------------------
PyNPA
~~~~~
.. automodule:: pybel.io.pynpa

.. autofunction:: pybel.to_npa_directory
.. autofunction:: pybel.to_npa_dfs

HiPathia
~~~~~~~~
.. automodule:: pybel.io.hipathia

.. autofunction:: pybel.to_hipathia
.. autofunction:: pybel.to_hipathia_dfs

.. autofunction:: pybel.from_hipathia_paths
.. autofunction:: pybel.from_hipathia_dfs

SPIA
~~~~
.. automodule:: pybel.io.spia

.. autofunction:: pybel.to_spia_dfs
.. autofunction:: pybel.to_spia_excel
.. autofunction:: pybel.to_spia_tsvs

PyKEEN
~~~~~~
.. automodule:: pybel.io.pykeen

.. autofunction:: pybel.io.pykeen.get_triples_from_bel
.. autofunction:: pybel.io.pykeen.get_triples_from_bel_nodelink
.. autofunction:: pybel.io.pykeen.get_triples_from_bel_pickle
.. autofunction:: pybel.io.pykeen.get_triples_from_bel_commons

Machine Learning
~~~~~~~~~~~~~~~~
.. automodule:: pybel.io.triples

.. autofunction:: pybel.to_triples
.. autofunction:: pybel.to_triples_file
.. autofunction:: pybel.to_edgelist

Web Services
------------
BEL Commons
~~~~~~~~~~~
.. automodule:: pybel.io.bel_commons_client

.. autofunction:: pybel.from_bel_commons
.. autofunction:: pybel.to_bel_commons

Amazon Simple Storage Service (S3)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. automodule:: pybel.io.aws

.. autofunction:: pybel.to_s3
.. autofunction:: pybel.from_s3

BioDati
~~~~~~~
.. automodule:: pybel.io.biodati_client

.. autofunction:: pybel.to_biodati
.. autofunction:: pybel.from_biodati

Fraunhofer OrientDB
~~~~~~~~~~~~~~~~~~~
.. automodule:: pybel.io.fraunhofer_orientdb

.. autofunction:: pybel.from_fraunhofer_orientdb

EMMAA
~~~~~~
.. automodule:: pybel.io.emmaa

.. autofunction:: pybel.from_emmaa

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

Lossy Export
------------
Umbrella Node-Link JSON
~~~~~~~~~~~~~~~~~~~~~~~
.. automodule:: pybel.io.umbrella_nodelink

.. autofunction:: pybel.to_umbrella_nodelink
.. autofunction:: pybel.to_umbrella_nodelink_file
.. autofunction:: pybel.to_umbrella_nodelink_gz

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
