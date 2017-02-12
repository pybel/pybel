"""

PyBEL is tested on both Python3 and legacy Python2 installations on Mac OS and Linux.

.. warning:: PyBEL is not thoroughly tested on Windows.

Installation
------------

Easiest
~~~~~~~

.. code-block:: sh

   $ pip3 install pybel

Get the Latest
~~~~~~~~~~~~~~~

.. code-block:: sh

   $ pip3 install git+https://github.com/pybel/pybel.git@develop

For Developers
~~~~~~~~~~~~~~

.. code-block:: sh

   $ git clone https://github.com/pybel/pybel.git@develop
   $ cd pybel
   $ pip3 install -e .


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

from . import io
from .canonicalize import to_bel
from .graph import BELGraph
from .io import *
from .manager.graph_cache import to_database, from_database

__all__ = ['BELGraph', 'to_database', 'from_database', 'to_bel'] + list(io.__all__)

__version__ = '0.3.8'

__title__ = 'PyBEL'
__description__ = 'Parsing, validation, and analysis of BEL graphs'
__url__ = 'https://github.com/pybel/pybel'

__author__ = 'Charles Tapley Hoyt, Andrej Konotopez, Christian Ebeling'
__email__ = 'charles.hoyt@scai.fraunhofer.de'

__license__ = 'Apache 2.0 License'
__copyright__ = 'Copyright (c) 2016 Charles Tapley Hoyt, Andrej Konotopez, Christian Ebeling'
