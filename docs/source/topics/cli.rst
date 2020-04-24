Command Line Interface
======================
.. note:: The command line wrapper might not work on Windows. Use :code:`python3 -m pybel` if it has issues.

PyBEL automatically installs the command :code:`pybel`. This command can be used to easily compile BEL documents
and convert to other formats. See :code:`pybel --help` for usage details. This command makes logs of all conversions
and warnings to the directory :code:`~/.pybel/`.

.. click:: pybel.cli:main
   :prog: pybel
   :show-nested:
