Getting Started
===============

Installation
------------

1. Get the code. Either clone/fork/branch from GitHub using :code:`git` or unzip your archive.

.. code-block:: sh

    git clone https://github.com/cthoyt/pybel.git


2. :code:`cd` into your directory

.. code-block:: sh

    cd pybel


3. Install with :code:`pip`. If you want to make changes, add :code:`-e` before the dot

.. code-block:: sh

   pip install .


4. Check that all tests are passing

.. code-block:: sh

   tox


Basic Usage
-----------

Command Line Usage
~~~~~~~~~~~~~~~~~~

PyBEL automatically installs the command :code:`pybel`. This command can be used to easily compile BEL documents
and convert to other formats. See :code:`pybel --help` for usage details. This command makes logs of all conversions
and warnings to the directory :code:`~/.pybel/`.

Load, compile, and export to Cytoscape format:

.. code-block:: sh

    $ pybel to_graphml --path ~/Desktop/example.bel --output ~/Desktop/example.graphml

In Cytoscape, open with :code:`Import > Network > From File`.


Python API
~~~~~~~~~~

The most useful functions for users are exposed at the top level package. These functions allow for easy import
from URL, file, iterable, or a database. It also includes various export options.

.. code-block:: python

   >>> import pybel, networkx
   >>> g = pybel.from_url('http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel')
   >>> networkx.draw(g)

.. automodule:: pybel
    :members:
