Logging Messages
================

Errors
------

These errors are produced when PyBEL cannot continue parsing, because of a technical problem, or unsalvagable
syntatic/semantic problem. These are logged at the CRITICAL level.

.. automodule:: pybel.exceptions
    :members:

Warnings
--------

A message for "General Parser Failure" is displayed when a problem was caused due to an unforseen error. The line
number and original statement are printed for the user to debug.

When errors in the statement leave the term or relation as nonsense, these errors are thrown and the statement is
excluded. These are logged at the ERROR level with code :code:`PyBEL1XX`.

.. automodule:: pybel.parser.parse_exceptions
    :members:
