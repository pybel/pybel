PyBEL |develop_build| |develop_windows_build| |develop_coverage| |develop_documentation| |zenodo|
=================================================================================================
`PyBEL <http://pybel.readthedocs.io>`_ is a Python package for parsing and handling biological networks encoded in the
`Biological Expression Language <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html>`_ (BEL).
It also facilitates data interchange between common formats and databases such as
`NetworkX <http://networkx.github.io/>`_, JSON, CSV, SIF, `Cytoscape <http://www.cytoscape.org/>`_,
`CX <http://www.home.ndexbio.org/data-model/>`_, `NDEx <https://github.com/pybel/pybel2cx>`_, SQL, and
`Neo4J <https://neo4j.com>`_.

Its companion package, `PyBEL Tools <http://pybel-tools.readthedocs.io/>`_, contains a
suite of functions and workflows for analyzing the resulting biological networks.

Citation
--------
If you use PyBEL in your work, we ask that you please cite:

Hoyt et al., 2017. PyBEL: a computational framework for Biological Expression Language. Bioinformatics, btx660, https://doi.org/10.1093/bioinformatics/btx660

Getting Started
---------------
In this example, the
`Selventa Small Corpus <https://wiki.openbel.org/display/home/Summary+of+Large+and+Small+BEL+Corpuses>`_ is loaded and
visualized in a Jupyter Notebook.

.. code-block:: python

   >>> import pybel, pybel_tools
   >>> graph = pybel.from_url('http://resources.openbel.org/belframework/20150611/knowledge/small_corpus.bel')
   >>> graph.number_of_nodes()  # Will be smaller than expected because we have the most strict settings enabled
   1207
   >>> pybel_tools.visualization.to_jupyter(graph)

More examples can be found in the `documentation <http://pybel.readthedocs.io>`_ and in the
`PyBEL Notebooks <https://github.com/pybel/pybel-notebooks>`_ repository.

PyBEL also installs a command line interface with the command :code:`pybel` for simple utilities such as data
conversion. In this example, a BEL Script is exported to GraphML for viewing in Cytoscape.

.. code-block:: sh

    $ pybel convert --path ~/Desktop/example.bel --graphml ~/Desktop/example.graphml
   
In Cytoscape, open with :code:`Import > Network > From File`.

Installation |pypi_version| |python_versions| |pypi_license|
------------------------------------------------------------
PyBEL can be installed easily from `PyPI <https://pypi.python.org/pypi/pybel>`_ with the following code in
your favorite terminal:

.. code-block:: sh

    $ python3 -m pip install pybel

or from the latest code on `GitHub <https://github.com/pybel/pybel>`_ with:

.. code-block:: sh

    $ python3 -m pip install git+https://github.com/pybel/pybel.git@develop

See the `installation documentation <http://pybel.readthedocs.io/en/latest/installation.html>`_ for more advanced
instructions. Also, check the change log at :code:`CHANGELOG.rst`.

Contributing
------------
Contributions, whether filing an issue, making a pull request, or forking, are appreciated. See
:code:`CONTRIBUTING.rst` for more information on getting involved. Please add your name to :code:`AUTHORS.rst`!

Acknowledgements
----------------
- This package was originally developed as part of the master's work of
  `Charles Tapley Hoyt <https://github.com/cthoyt>`_ at `Fraunhofer SCAI <https://www.scai.fraunhofer.de/>`_ with
  partial support from the `IMI <https://www.imi.europa.eu/>`_ projects: `AETIONOMY <http://www.aetionomy.eu/>`_ and
  `PHAGO <http://www.phago.eu/>`_.
- This software is proudly built with Paul McGuire's `PyParsing <http://pyparsing.wikispaces.com/>`_ package.
- `Scott Colby <https://github.com/scolby33>`_ designed our `logo <https://github.com/pybel/pybel-art>`_ and provided
  sage advice
- `Christian Ebeling <https://github.com/cebel>`_ for supervision and consultation

Links
-----
- Specified by `BEL 1.0 <http://openbel.org/language/version_1.0/bel_specification_version_1.0.html>`_ and
  `BEL 2.0 <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html>`_
- Documented on `Read the Docs <http://pybel.readthedocs.io/>`_
- Versioned on `GitHub <https://github.com/pybel/pybel>`_
- Tested on `Travis CI <https://travis-ci.org/pybel/pybel>`_
- Distributed by `PyPI <https://pypi.python.org/pypi/pybel>`_
- Chat on `Gitter <https://gitter.im/pybel/Lobby>`_

.. |stable_build| image:: https://travis-ci.org/pybel/pybel.svg?branch=master
    :target: https://travis-ci.org/pybel/pybel
    :alt: Stable Build Status

.. |stable_coverage| image:: https://codecov.io/gh/pybel/pybel/coverage.svg?branch=master
    :target: https://codecov.io/gh/pybel/pybel?branch=master
    :alt: Stable Coverage Status

.. |stable_documentation| image:: https://readthedocs.org/projects/pybel/badge/?version=stable
    :target: http://pybel.readthedocs.io/en/stable/
    :alt: Stable Documentation Status

.. |develop_build| image:: https://travis-ci.org/pybel/pybel.svg?branch=develop
    :target: https://travis-ci.org/pybel/pybel
    :alt: Development Build Status

.. |develop_windows_build| image:: https://ci.appveyor.com/api/projects/status/v22l3ymg3bdq525d/branch/develop?svg=true
    :target: https://ci.appveyor.com/project/cthoyt/pybel
    :alt: Development Windows Build Status

.. |develop_coverage| image:: https://codecov.io/gh/pybel/pybel/coverage.svg?branch=develop
    :target: https://codecov.io/gh/pybel/pybel?branch=develop
    :alt: Development Coverage Status

.. |develop_documentation| image:: https://readthedocs.org/projects/pybel/badge/?version=latest
    :target: http://pybel.readthedocs.io/en/latest/
    :alt: Development Documentation Status

.. |climate| image:: https://codeclimate.com/github/pybel/pybel/badges/gpa.svg
    :target: https://codeclimate.com/github/pybel/pybel
    :alt: Code Climate

.. |python_versions| image:: https://img.shields.io/pypi/pyversions/PyBEL.svg
    :alt: Stable Supported Python Versions

.. |pypi_version| image:: https://img.shields.io/pypi/v/PyBEL.svg
    :alt: Current version on PyPI

.. |pypi_license| image:: https://img.shields.io/pypi/l/PyBEL.svg
    :alt: Apache 2.0 License

.. |zenodo| image:: https://zenodo.org/badge/68376693.svg
    :target: https://zenodo.org/badge/latestdoi/68376693