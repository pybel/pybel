Cookbook
========

An extensive set of examples can be found on the `PyBEL Notebooks <https://github.com/pybel/pybel-notebooks>`_
repository on GitHub. These notebooks contain basic usage and also make numerous references to the analytical
package `PyBEL Tools <https://github.com/pybel/pybel-tools>`_

Configuration
-------------

The default connection string can be set as an environment variable in your ``~/.bashrc``. If you're using MySQL or
MariaDB, it could look like this:

.. code::

    $ export PYBEL_CONNECTION="mysql+pymysql://user:password@server_name/database_name?charset=utf8"

Command Line
------------

.. note:: The command line wrapper might not work on Windows. Use :code:`python3 -m pybel` if it has issues.

PyBEL automatically installs the command :code:`pybel`. This command can be used to easily compile BEL documents
and convert to other formats. See :code:`pybel --help` for usage details. This command makes logs of all conversions
and warnings to the directory :code:`~/.pybel/`.

Prepare a Cytoscape Network
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Load, compile, and export to Cytoscape format:

.. code-block:: sh

    $ pybel convert --path ~/Desktop/example.bel --graphml ~/Desktop/example.graphml

In Cytoscape, open with :code:`Import > Network > From File`.
