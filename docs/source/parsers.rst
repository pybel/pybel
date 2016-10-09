Parsers
=======

PyBEL makes extensive use of the PyParsing module. The code is organized to different modules to reflect
the different faces ot the BEL language. These parsers support BEL 2.0 and have some backwards compatability
for rewriting BEL 1.0 statements as BEL 2.0.

See: https://github.com/OpenBEL/language/blob/master/version_2.0/MIGRATE_BEL1_BEL2.md

Control Parser
--------------
This module handles parsing control statement, which add annotations and namespaces to the document.

See: https://wiki.openbel.org/display/BLD/Control+Records

.. autoclass:: pybel.parser.parse_control.ControlParser
    :members:

Relation Parser
---------------
.. autoclass:: pybel.parser.parse_bel.BelParser
    :members:

Metadata Parser
---------------
This module supports the relation parser by handling statements

.. autoclass:: pybel.parser.parse_metadata.MetadataParser
    :members:
