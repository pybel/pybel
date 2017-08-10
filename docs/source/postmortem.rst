Current Issues
==============

Speed
-----
Speed is still an issue, because documents above 100K lines still take a couple minutes to run. This issue is
  exacerbated by (optionally) logging output to the console, which can make it more than 3x or 4x as slow.

Namespaces
----------
The default namespaces from OpenBEL do not follow a standard file format. They are similar to INI config files,
but do not use consistent delimiters. Also, many of the namespaces don't respect that the delimiter should not
be used in the namespace names. There are also lots of names with strange characters, which may have been caused
by copying from a data source that had specfic escape characters without proper care.

Testing
-------
Testing was very difficult because the example documents on the OpenBEL website had many semantic errors, such as
using names and annotation values that were not defined within their respective namespace and annotation definition
files. They also contained syntax errors like naked names, which are not only syntatically incorrect, but lead to
bad science; and improper usage of activities, like illegally nesting an activity within a composite statement.