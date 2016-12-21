Reference
=========

Top-Level API
-------------
.. automodule:: pybel
    :members:

Parsers
-------
PyBEL makes extensive use of the PyParsing module. The code is organized to different modules to reflect
the different faces ot the BEL language. These parsers support BEL 2.0 and have some backwards compatability
for rewriting BEL 1.0 statements as BEL 2.0. The biologist and bioinformatician using this software will likely never
need to read this page, but a developer seeking to extend the language will be interested to see the inner workings
of these parsers.

See: https://github.com/OpenBEL/language/blob/master/version_2.0/MIGRATE_BEL1_BEL2.md

Control Parser
~~~~~~~~~~~~~~
This module handles parsing control statement, which add annotations and namespaces to the document.

See: https://wiki.openbel.org/display/BLD/Control+Records

.. autoclass:: pybel.parser.parse_control.ControlParser
    :members:

Relation Parser
~~~~~~~~~~~~~~~
This module handles parsing BEL relations and validation of semantics.

.. autoclass:: pybel.parser.parse_bel.BelParser
    :members:

Metadata Parser
~~~~~~~~~~~~~~~
This module supports the relation parser by handling statements.

.. autoclass:: pybel.parser.parse_metadata.MetadataParser
    :members:

Data Management
---------------

Under the hood, PyBEL caches namespace and annotation files for quick recall on later use. The user doesn't need to
enable this option, but can specifiy a specific database location if they choose.

Managers
~~~~~~~~

.. automethod:: pybel.manager.cache.CacheManager.__init__

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

