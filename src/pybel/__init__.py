# -*- coding: utf-8 -*-

"""

PyBEL is tested on both Python3 and legacy Python2 installations on Mac OS and Linux using 
`Travis CI <https://travis-ci.org/pybel/pybel>`_.

.. warning:: PyBEL is not thoroughly tested on Windows.

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


Caveats
-------

- PyBEL extends the :code:`networkx` for its core data structure. Many of the graphical aspects of :code:`networkx`
  depend on :code:`matplotlib`, which is an optional dependency.
- If :code:`HTMLlib5` is installed, the test that's supposed to fail on a web page being missing actually tries to
  parse it as RDFa, and doesn't fail. Disregard this.

Upgrading
---------

During the current development cycle, programmatic access to the definition and graph caches might become unstable. If 
you have any problems working with the database, try removing it either by 

1. Running :code:`pybel manage remove` (unix)
2. Running :code:`python3 -m pybel manage remove` (windows)
3. Removing the folder :code:`~/.pybel`

PyBEL will build a new database and populate it on the next run.
"""

from . import canonicalize
from . import constants
from . import io
from . import struct
from .canonicalize import *
from .io import *
from .manager import database_io
from .manager.database_io import *
from .struct import *

__all__ = (
    struct.__all__ +
    io.__all__ +
    canonicalize.__all__ +
    database_io.__all__
)

__version__ = '0.6.0'

__title__ = 'PyBEL'
__description__ = 'Parsing, validation, and data exchange of BEL graphs'
__url__ = 'https://github.com/pybel/pybel'

__author__ = 'Charles Tapley Hoyt'
__email__ = 'charles.hoyt@scai.fraunhofer.de'

__license__ = 'Apache 2.0 License'
__copyright__ = 'Copyright (c) 2017 Charles Tapley Hoyt'
