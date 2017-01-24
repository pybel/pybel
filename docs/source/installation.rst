Installation
============

For end users:

.. code-block:: sh

   pip install pybel

For the latest and greatest:

.. code-block:: sh

   pip install git+https://github.com/pybel/pybel.git@develop

For development:

.. code-block:: sh

   git clone https://github.com/pybel/pybel.git@develop
   cd pybel
   pip install -e .

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
try to remove the database either by deleting the file in :code:`~/.pybel/data/cache.db` or by running
:code:`pybel manage remove` from the command line.

Future versions of PyBEL will include database integrity checks and provide upgrade procedures/scripts.
