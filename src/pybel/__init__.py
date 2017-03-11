"""

PyBEL is tested on both Python3 and legacy Python2 installations on Mac OS and Linux.

.. warning:: PyBEL is not thoroughly tested on Windows.

Installation
------------

Easiest
~~~~~~~

.. code-block:: sh

   $ python3 -m pip install pybel

Get the Latest
~~~~~~~~~~~~~~~

.. code-block:: sh

   $ python3 -m pip install git+https://github.com/pybel/pybel.git@develop

For Developers
~~~~~~~~~~~~~~

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

During the current development cycle, many models are being added and changed in the PyBEL schema. This might make
programmatic access to the database with SQLAlchemy unstable. If you have any problems working with the database,
try to remove it by running :code:`pybel manage remove` from the command line. PyBEL will build
a new database and populate it on the next run.

Future versions of PyBEL will include database integrity checks and provide upgrade procedures/scripts.
"""

from . import canonicalize
from . import constants
from . import cx
from . import io
from .canonicalize import *
from .cx import *
from .graph import BELGraph
from .io import *
from .manager import database_io
from .manager.database_io import *

__all__ = ['BELGraph'] + io.__all__ + canonicalize.__all__ + cx.__all__ + database_io.__all__

__version__ = '0.4.1'

__title__ = 'PyBEL'
__description__ = 'Parsing, validation, and data exchange of BEL graphs'
__url__ = 'https://github.com/pybel/pybel'

__author__ = 'Charles Tapley Hoyt'
__email__ = 'charles.hoyt@scai.fraunhofer.de'

__license__ = 'Apache 2.0 License'
__copyright__ = 'Copyright (c) 2017 Charles Tapley Hoyt'
