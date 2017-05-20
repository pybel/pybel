Input and Output
================

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

Bytes
~~~~~
.. autofunction:: pybel.to_pickle
.. autofunction:: pybel.from_pickle
.. autofunction:: pybel.to_bytes
.. autofunction:: pybel.from_bytes

Node Link JSON
~~~~~~~~~~~~~~
.. autofunction:: pybel.to_json
.. autofunction:: pybel.from_json

.. autofunction:: pybel.from_json_file
.. autofunction:: pybel.from_json_file

.. autofunction:: pybel.to_jsons
.. autofunction:: pybel.from_jsons

CX JSON
~~~~~~~
.. autofunction:: pybel.to_cx
.. autofunction:: pybel.from_cx

.. autofunction:: pybel.to_cx_file
.. autofunction:: pybel.from_cx_file

.. autofunction:: pybel.to_cx_jsons
.. autofunction:: pybel.from_cx_jsons


Export
------
.. autofunction:: pybel.to_graphml
.. autofunction:: pybel.to_csv
.. autofunction:: pybel.to_neo4j

Relational Database
-------------------
.. autofunction:: pybel.to_database
.. autofunction:: pybel.from_database
