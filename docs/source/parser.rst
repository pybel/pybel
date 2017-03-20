Parser Reference
================

This page is for users who want to squeeze the most bizarre possibilities out of PyBEL. Most users will not need this
reference.

PyBEL makes extensive use of the PyParsing module. The code is organized to different modules to reflect
the different faces ot the BEL language. These parsers support BEL 2.0 and have some backwards compatability
for rewriting BEL 1.0 statements as BEL 2.0. The biologist and bioinformatician using this software will likely never
need to read this page, but a developer seeking to extend the language will be interested to see the inner workings
of these parsers.

See: https://github.com/OpenBEL/language/blob/master/version_2.0/MIGRATE_BEL1_BEL2.md

Control Parser
--------------
.. autoclass:: pybel.parser.parse_control.ControlParser
    :members:

Metadata Parser
---------------
.. autoclass:: pybel.parser.parse_metadata.MetadataParser
    :members:

BEL Parser
----------
.. autoclass:: pybel.parser.parse_bel.BelParser
    :members:
