Command Line
============

.. warning:: This feature might not work on Windows

PyBEL automatically installs the command :code:`pybel`. This command can be used to easily compile BEL documents
and convert to other formats. See :code:`pybel --help` for usage details. This command makes logs of all conversions
and warnings to the directory :code:`~/.pybel/`.

Error Analysis
--------------

In this example, a local file is parsed and output to both GraphML and a Python pickle object for later. The logging
is output as well, for error triaging with grep. This example makes use of the logging message codes, which are
mentioned later in the documentation.

.. code-block:: sh

    #!/usr/bin/env bash
    pybel convert --path PD_Aetionomy.bel 2> log.txt

    cat log.txt | grep "NakedNameWarning" > ~/bel/PD_nakedNames.txt
    cat log.txt | grep "ERROR" > ~/bel/PD_errors.txt


Prepare a Cytoscape Network
---------------------------

Load, compile, and export to Cytoscape format:

.. code-block:: sh

    $ pybel convert --path ~/Desktop/example.bel --graphml ~/Desktop/example.graphml

In Cytoscape, open with :code:`Import > Network > From File`.
