Input and Output
================

PyBEL contains multiple input and output methods. All transport pairs are data-preserving.

Import
------
.. autofunction:: pybel.from_lines
.. autofunction:: pybel.from_path
.. autofunction:: pybel.from_url
.. autofunction:: pybel.to_bel

Transport
---------
.. autofunction:: pybel.to_pickle
.. autofunction:: pybel.from_pickle
.. autofunction:: pybel.to_json
.. autofunction:: pybel.from_json
.. autofunction:: pybel.to_cx_json
.. autofunction:: pybel.from_cx_json


Export Only
-----------

.. autofunction:: pybel.to_graphml
.. autofunction:: pybel.to_csv
.. autofunction:: pybel.to_neo4j
