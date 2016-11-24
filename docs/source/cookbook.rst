Cookbook
========

Command Line Usage
------------------

PyBEL automatically installs the command :code:`pybel`. This command can be used to easily compile BEL documents
and convert to other formats. See :code:`pybel --help` for usage details. This command makes logs of all conversions
and warnings to the directory :code:`~/.pybel/`.

Load, compile, and export to Cytoscape format:

.. code-block:: sh

    $ pybel convert --path ~/Desktop/example.bel --graphml ~/Desktop/example.graphml

In Cytoscape, open with :code:`Import > Network > From File`.

Example Workflow
~~~~~~~~~~~~~~~~

In this example, a local file is parsed and output to both GraphML and a Python pickle object for later. The logging
is output as well, for error triaging with grep. This example makes use of the logging message codes, which are
mentioned later in the documentation.

.. code-block:: sh

    #!/usr/bin/env bash
    pybel convert --path ~/ownCloud/BEL/PD_Aetionomy.bel \
            --graphml ~/bel/PD.graphml --pickle ~/bel/PD.gpickle \
            --log-file ~/bel/PD_log.txt

    cat ~/bel/PD_log.txt | grep "ERROR" > ~/bel/PD_errors.txt
    cat ~/bel/PD_log.txt | grep "PyBEL1" > ~/bel/PD_caught.txt
    cat ~/bel/PD_log.txt | grep "PyBEL121" | cut -d "-" -f 6,8 | tr '-' '\t' > ~/bel/PD_missing_ns.tsv

Python API
----------
PyBEL has a programmatic API for analysis using the swath of tools provided by PyBEL, NetworkX, and the community of
python programmers in Network Science. The most useful functions for users are exposed at the top level package.
These functions allow for easy import from URL, file, iterable, or a database. It also includes various export options.

Draw NetworkX and MatplotLib
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   >>> import pybel, networkx
   >>> url = 'http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel'
   >>> g = pybel.from_url(url)  # takes about 20 seconds
   >>> networkx.draw(g)

Export to Neo4j
~~~~~~~~~~~~~~~

.. code-block:: python

   >>> import pybel, py2neo
   >>> url = 'http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel'
   >>> g = pybel.from_url(url)
   >>> neo_graph = py2neo.Graph("http://localhost:7474/db/data/")  # use your own connection settings
   >>> pybel.to_neo4j(g, neo_graph)