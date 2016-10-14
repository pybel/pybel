Logging Messages
================

Catch-All
---------

General Parser Failure
~~~~~~~~~~~~~~~~~~~~~~
This message is displayed when a problem was caused due to an unforseen error. The line number and original statement
are printed for the user to debug.


Exceptions
----------

When errors in the statement leave the term or relation as nonsense, these errors are thrown and the statement is
excluded.


.. automodule:: pybel.parser.parse_exceptions
    :members:


Debug
-----

There are certain statements that aren't correct, but PyBEL can understand and fix. These will be handled automatically,
and a nice message with :code:`PyBELXXX` number will be output to debug.

PyBEL001
~~~~~~~~
Message: Legacy activity statement. Use activity() instead.

This means that an old style activity, like kin(p(HGNC:YFG)) was used. PyBEL converts this automatically to
activity(HGNC:YFG, molecularActivity(KinaseActivity))

PyBEL005
~~~~~~~~
Message: Legacy translocation statement. use fromLoc() and toLoc()

In BEL 1.0, translocation statements didn't have the qualifiers fromLoc and toLoc. PyBEL
adds these for you.


PyBEL006
~~~~~~~~
Message: deprecated protein substitution function. User variant() instead

Old protein substitutions are converted automatically to new HGVS style.

PyBEL009
~~~~~~~~
Message: old SNP annotation. Use variant() instead

Old gene substitutions are convert automatically to ne HGVS style.

PyBEL020
~~~~~~~~
Message: Can't unset missing key

This doesn't throw an error, but could mean there's a typo and could have unintended consequences for the
resulting BEL graph.