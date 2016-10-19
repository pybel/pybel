Logging Messages
================

Errors
------

These errors are produced when PyBEL cannot continue parsing, because of a technical problem, or unsalvagable
syntatic/semantic problem. These are logged at the CRITICAL level.

.. automodule:: pybel.exceptions
    :members:

Exceptions
----------

A message for "General Parser Failure" is displayed when a problem was caused due to an unforseen error. The line
number and original statement are printed for the user to debug.

When errors in the statement leave the term or relation as nonsense, these errors are thrown and the statement is
excluded. These are logged at the ERROR level with code :code:`PyBEL1XX`.

.. automodule:: pybel.parser.parse_exceptions
    :members:

Tracing
-------

There are certain statements that aren't correct, but PyBEL can understand and fix. These will be handled automatically,
and are logged at the TRACE level with :code:`PyBEL0XX` number will be output to debug.

+------+---------------------------+------------------------------------------------------------------------------------+
| Code | Problem                   | Explanation                                                                        |
+------+---------------------------+------------------------------------------------------------------------------------+
| 001  | Legacy molecular activity | This means that an old style activity, like kin(p(HGNC:YFG)) was used.             |
|      |                           |                                                                                    |
|      |                           | PyBEL converts this automatically to activity(HGNC:YFG, ma(KinaseActivity))        |
+------+---------------------------+------------------------------------------------------------------------------------+
| 016  | Legacy pmod()             | Old single-letter names have been deprecated in favor of more informative names.   |
|      |                           | See: BelSpecPmod_                                                                  |
+------+---------------------------+------------------------------------------------------------------------------------+
| 006  | Legacy sub()              | Attribute sub() in p() has been deprecated in favor of variant() and HGVS style.   |
|      |                           | Old protein substitutions are convert automatically to the new HGVS style.         |
+------+---------------------------+------------------------------------------------------------------------------------+
| 009  | Legacy sub()              | Attribute sub() in g() has been deprecated in favor of variant() and HGVS style.   |
|      |                           | Old gene substitutions are convert automatically to the new HGVS style.            |
+------+---------------------------+------------------------------------------------------------------------------------+
| 024  | Missing Key               | Tried to UNSET annotation that is not set                                          |
+------+---------------------------+------------------------------------------------------------------------------------+
| 025  | Legacy trunc()            | Attribute trunc() in p() has been deprecated in favor of variant() and HGVS style. |
+------+---------------------------+------------------------------------------------------------------------------------+

.. _BelSpecPmod: http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_modification_types_provided_in_default_bel_namespace