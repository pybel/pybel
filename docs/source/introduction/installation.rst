Installation
============
The latest stable code can be installed from `PyPI <https://pypi.python.org/pypi/pybel>`_ with:

.. code-block:: sh

   $ python3 -m pip install pybel

The most recent code can be installed from the source on `GitHub <https://github.com/pybel/pybel>`_ with:

.. code-block:: sh

   $ python3 -m pip install git+https://github.com/pybel/pybel.git

For developers, the repository can be cloned from `GitHub <https://github.com/pybel/pybel>`_ and installed in editable
mode with:

.. code-block:: sh

   $ git clone https://github.com/pybel/pybel.git
   $ cd pybel
   $ python3 -m pip install -e .

Extras
------
The ``setup.py`` makes use of the ``extras_require`` argument of :func:`setuptools.setup` in order to make some heavy
packages that support special features of PyBEL optional to install, in order to make the installation more lean by
default. A single extra can be installed from PyPI like :code:`python3 -m pip install pybel[neo4j]` or multiple can
be installed using a list like :code:`python3 -m pip install pybel[neo4j,indra]`. Likewise, for developer
installation, extras can be installed in editable mode with :code:`python3 -m pip install -e .[neo4j]` or multiple can
be installed using a list like :code:`python3 -m pip install -e .[neo4j,indra]`. The available extras are:

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

jupyter
~~~~~~~
This extra installs support for visualizing BEL graphs in Jupyter notebooks.

.. seealso::

    - :func:`pybel.io.jupyter.to_html`
    - :func:`pybel.io.jupyter.to_jupyter`

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
