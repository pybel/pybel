Input and Output
================

.. automodule:: pybel.io

Import
------
.. autofunction:: pybel.from_lines
.. autofunction:: pybel.from_path
.. autofunction:: pybel.from_url

Canonicalization
----------------
.. autofunction:: pybel.to_bel_lines
.. autofunction:: pybel.to_bel
.. autofunction:: pybel.to_bel_path

Transport
---------
All transport pairs are reflective and data-preserving.

.. automodule:: pybel.io.gpickle
.. autofunction:: pybel.from_pickle
.. autofunction:: pybel.to_pickle
.. autofunction:: pybel.from_bytes
.. autofunction:: pybel.to_bytes

.. automodule:: pybel.io.nodelink
.. autofunction:: pybel.from_json
.. autofunction:: pybel.to_json
.. autofunction:: pybel.from_json_file
.. autofunction:: pybel.to_json_file
.. autofunction:: pybel.from_jsons
.. autofunction:: pybel.to_jsons

.. automodule:: pybel.io.jgif
.. autofunction:: pybel.from_jgif
.. autofunction:: pybel.from_cbn_jgif
.. autofunction:: pybel.to_jgif

.. automodule:: pybel.io.cx
.. autofunction:: pybel.from_cx
.. autofunction:: pybel.to_cx
.. autofunction:: pybel.from_cx_file
.. autofunction:: pybel.to_cx_file
.. autofunction:: pybel.from_cx_jsons
.. autofunction:: pybel.to_cx_jsons

Export
------
.. autofunction:: pybel.to_graphml
.. autofunction:: pybel.to_csv
.. autofunction:: pybel.to_sif
.. autofunction:: pybel.to_gsea


Database
--------
.. automodule:: pybel.manager.database_io
.. autofunction:: pybel.from_database
.. autofunction:: pybel.to_database

.. automodule:: pybel.io.neo4j
.. autofunction:: pybel.to_neo4j

.. automodule:: pybel.io.ndex_utils
.. autofunction:: pybel.from_ndex
.. autofunction:: pybel.to_ndex
