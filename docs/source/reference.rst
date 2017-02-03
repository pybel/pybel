Reference
=========

Parsers
-------
PyBEL makes extensive use of the PyParsing module. The code is organized to different modules to reflect
the different faces ot the BEL language. These parsers support BEL 2.0 and have some backwards compatability
for rewriting BEL 1.0 statements as BEL 2.0. The biologist and bioinformatician using this software will likely never
need to read this page, but a developer seeking to extend the language will be interested to see the inner workings
of these parsers.

See: https://github.com/OpenBEL/language/blob/master/version_2.0/MIGRATE_BEL1_BEL2.md

.. autoclass:: pybel.parser.parse_control.ControlParser
    :members:


.. autoclass:: pybel.parser.parse_bel.BelParser
    :members:

.. autoclass:: pybel.parser.parse_metadata.MetadataParser
    :members:

Data Management
---------------

.. autoclass:: pybel.manager.cache.CacheManager
    :members:

Utilities
---------

Some utilities that are used throughout the software are explained here:

General Utilities
~~~~~~~~~~~~~~~~~

.. automodule:: pybel.utils
    :members:

Parser Utilities
~~~~~~~~~~~~~~~~

.. automodule:: pybel.parser.utils
    :members:

