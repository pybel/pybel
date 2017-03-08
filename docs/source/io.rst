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

.. autofunction:: pybel.to_pickle
.. autofunction:: pybel.from_pickle
.. autofunction:: pybel.to_json
.. autofunction:: pybel.from_json
.. autofunction:: pybel.to_cx_json
.. autofunction:: pybel.from_cx_json

Export
------
.. autofunction:: pybel.to_graphml
.. autofunction:: pybel.to_csv
.. autofunction:: pybel.to_neo4j
