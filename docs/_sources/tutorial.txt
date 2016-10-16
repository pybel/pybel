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

   python -m pip install -U .

This is a good chance to upgrade your pip and setuptools as well with

.. code-block:: sh

    python -m pip install -U setuptools pip wheel


4. If you're a developer and don't mind googling to figure out problems, check that all tests are passing:

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

    $ pybel convert --path ~/Desktop/example.bel --graphml ~/Desktop/example.graphml

In Cytoscape, open with :code:`Import > Network > From File`.

Example Workflow
~~~~~~~~~~~~~~~~

.. code-block:: sh

    #!/usr/bin/env bash
    python3 -m pybel convert --path ~/Downloads/PD_Aetionomy.bel --graphml ~/Downloads/PD.graphml --pickle ~/Downloads/PD.gpickle --log-file ~/Downloads/PD_log.txt

    cat ~/Downloads/PD_log.txt | grep ERROR > ~/Downloads/PD_log_errors.txt
    cat ~/Downloads/PD_log.txt | grep PyBEL1 > ~/Downloads/PD_log_caught.txt
    cat ~/Downloads/PD_log.txt | grep PyBEL121 | cut -d "-" -f 6,8 | tr '-' '\t' > ~/Downloads/PD_missing_namespaces.tsv

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
