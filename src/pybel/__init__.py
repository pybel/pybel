# -*- coding: utf-8 -*-

"""Parsing, validation, compilation, and data exchange of Biological Expression Language (BEL).

PyBEL is tested on both Python3 and legacy Python2 installations on Mac OS and Linux using
`Travis CI <https://travis-ci.org/pybel/pybel>`_ as well as on Windows using
`AppVeyor <https://ci.appveyor.com/project/cthoyt/pybel>`_.

Installation
------------
Easiest
~~~~~~~
Download the latest stable code from `PyPI <https://pypi.python.org/pypi/pybel>`_ with:

.. code-block:: sh

   $ python3 -m pip install pybel

Get the Latest
~~~~~~~~~~~~~~~
Download the most recent code from `GitHub <https://github.com/pybel/pybel>`_ with:

.. code-block:: sh

   $ python3 -m pip install git+https://github.com/pybel/pybel.git@develop

For Developers
~~~~~~~~~~~~~~
Clone the repository from `GitHub <https://github.com/pybel/pybel>`_ and install in editable mode with:

.. code-block:: sh

   $ git clone https://github.com/pybel/pybel.git@develop
   $ cd pybel
   $ python3 -m pip install -e .

Extras
------
The ``setup.py`` makes use of the ``extras_require`` argument of :func:`setuptools.setup` in order to make some heavy
packages that support special features of PyBEL optional to install, in order to make the installation more lean by
default. A single extra can be installed from PyPI like :code:`python3 -m pip install -e pybel[neo4j]` or multiple can
be installed using a list like :code:`python3 -m pip install -e pybel[neo4j,inra]`. Likewise, for developer installation,
extras can be installed in editable mode with :code:`python3 -m pip install -e .[neo4j]` or multiple can be installed
using a list like :code:`python3 -m pip install -e .[neo4j,indra]`. The available extras are:

neo4j
~~~~~
This extension installs the :mod:`py2neo` package to support upload and download to Neo4j databases.

.. seealso::

    - :func:`pybel.to_neo4j`

indra
~~~~~
This extra installs support for :mod:`indra`, the integrated network dynamical reasoner and assembler. Because it also
represents biology in BEL-like statements, many statements from PyBEL can be converted to INDRA, and visa-versa. This
package also enables the import of BioPAX, SBML, and SBGN into BEL.

.. seealso::

    - :func:`pybel.from_biopax`
    - :func:`pybel.from_indra_statements`
    - :func:`pybel.from_indra_pickle`
    - :func:`pybel.to_indra`

Caveats
-------
- PyBEL extends the :code:`networkx` for its core data structure. Many of the graphical aspects of :code:`networkx`
  depend on :code:`matplotlib`, which is an optional dependency.
- If :code:`HTMLlib5` is installed, the test that's supposed to fail on a web page being missing actually tries to
  parse it as RDFa, and doesn't fail. Disregard this.

Upgrading
---------
During the current development cycle, programmatic access to the definition and graph caches might become unstable. If 
you have any problems working with the database, try removing it with one of the following commands:

1. Running :code:`pybel manage drop` (unix)
2. Running :code:`python3 -m pybel manage drop` (windows)
3. Removing the folder :code:`~/.pybel`

PyBEL will build a new database and populate it on the next run.
"""

from . import canonicalize, constants, examples, examples, io, struct
from .canonicalize import *
from .examples import *
from .io import *
from .manager import cache_manager, database_io
from .manager.cache_manager import *
from .manager.database_io import *
from .struct import *
from .utils import get_version

__all__ = (
        struct.__all__ +
        io.__all__ +
        canonicalize.__all__ +
        database_io.__all__ +
        cache_manager.__all__ +
        examples.__all__ + [
            'get_version',
        ]
)

__version__ = '0.11.11'

__title__ = 'PyBEL'
__description__ = 'Parsing, validation, compilation, and data exchange of Biological Expression Language (BEL)'
__url__ = 'https://github.com/pybel/pybel'

__author__ = 'Charles Tapley Hoyt'
__email__ = 'charles.hoyt@scai.fraunhofer.de'

__license__ = 'Apache 2.0 License'
__copyright__ = 'Copyright (c) 2016-2018 Charles Tapley Hoyt'
