PyBEL |zenodo| |build| |windows_build| |coverage| |documentation|
=================================================================
`PyBEL <http://pybel.readthedocs.io>`_ is a pure Python package for parsing and handling biological networks encoded in
the `Biological Expression Language <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html>`_
(BEL). It also facilitates data interchange between common formats and databases such as
`NetworkX <http://networkx.github.io/>`_, JSON, CSV, SIF, `Cytoscape <http://www.cytoscape.org/>`_,
`CX <http://www.home.ndexbio.org/data-model/>`_, `NDEx <https://github.com/pybel/pybel2cx>`_, SQL, and
`Neo4J <https://neo4j.com>`_.

Its companion package, `PyBEL Tools <http://pybel-tools.readthedocs.io/>`_, contains a
suite of functions and pipelines for analyzing the resulting biological networks.

We realize there we have a name conflict with the python wrapper for the cheminformatics package, OpenBabel. If you're
looking for their python wrapper, see `here <https://github.com/openbabel/openbabel/tree/master/scripts/python>`_.

Citation
--------
If you find PyBEL useful for your work, please consider citing:

.. [1] Hoyt, C. T., *et al.* (2017). `PyBEL: a Computational Framework for Biological Expression Language
       <https://doi.org/10.1093/bioinformatics/btx660>`_. Bioinformatics, 34(December), 1–2.

Getting Started
---------------
This example illustrates how the a BEL document from the `Human Brain Pharmacome
<https://raw.githubusercontent.com/pharmacome/knowledge>`_ project can be loaded from GitHub.

.. code-block:: python

   >>> import pybel
   >>> url = 'https://raw.githubusercontent.com/pharmacome/knowledge/master/hbp_knowledge/proteostasis/kim2013.bel'
   >>> graph = pybel.from_url(url)

More examples can be found in the `documentation <http://pybel.readthedocs.io>`_ and in the
`PyBEL Notebooks <https://github.com/pybel/pybel-notebooks>`_ repository.

PyBEL also installs a command line interface with the command :code:`pybel` for simple utilities such as data
conversion. In this example, a BEL document is compiled then exported to `GraphML <http://graphml.graphdrawing.org/>`_
for viewing in Cytoscape.

.. code-block:: sh

    $ pybel compile ~/Desktop/example.bel
    $ pybel serialize ~/Desktop/example.bel --graphml ~/Desktop/example.graphml

In Cytoscape, open with :code:`Import > Network > From File`.

Installation |pypi_version| |python_versions| |pypi_license|
------------------------------------------------------------
PyBEL can be installed easily from `PyPI <https://pypi.python.org/pypi/pybel>`_ with the following code in
your favorite terminal:

.. code-block:: sh

    $ pip install pybel

or from the latest code on `GitHub <https://github.com/pybel/pybel>`_ with:

.. code-block:: sh

    $ pip install git+https://github.com/pybel/pybel.git

See the `installation documentation <http://pybel.readthedocs.io/en/latest/installation.html>`_ for more advanced
instructions. Also, check the change log at `CHANGELOG.rst <https://github.com/pybel/pybel/blob/develop/CHANGELOG.rst>`_.

Contributing
------------
Contributions, whether filing an issue, making a pull request, or forking, are appreciated. See
`CONTRIBUTING.rst <https://github.com/pybel/pybel/blob/develop/CONTRIBUTING.rst>`_ for more information on getting
involved. Please add your name to `AUTHORS.rst <https://github.com/pybel/pybel/blob/develop/AUTHORS.rst>`_!

Acknowledgements
----------------
- This package was originally developed as part of the master's work of
  `Charles Tapley Hoyt <https://github.com/cthoyt>`_ at `Fraunhofer SCAI <https://www.scai.fraunhofer.de/>`_.
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

.. |build| image:: https://travis-ci.org/pybel/pybel.svg?branch=develop
    :target: https://travis-ci.org/pybel/pybel
    :alt: Development Build Status

.. |windows_build| image:: https://ci.appveyor.com/api/projects/status/v22l3ymg3bdq525d/branch/develop?svg=true
    :target: https://ci.appveyor.com/project/cthoyt/pybel
    :alt: Development Windows Build Status

.. |coverage| image:: https://codecov.io/gh/pybel/pybel/coverage.svg?branch=develop
    :target: https://codecov.io/gh/pybel/pybel/branch/develop
    :alt: Development Coverage Status

.. |documentation| image:: https://readthedocs.org/projects/pybel/badge/?version=latest
    :target: http://pybel.readthedocs.io/en/latest/
    :alt: Development Documentation Status

.. |climate| image:: https://codeclimate.com/github/pybel/pybel/badges/gpa.svg
    :target: https://codeclimate.com/github/pybel/pybel
    :alt: Code Climate

.. |python_versions| image:: https://img.shields.io/pypi/pyversions/PyBEL.svg
    :target: https://pypi.python.org/pypi/pybel
    :alt: Stable Supported Python Versions

.. |pypi_version| image:: https://img.shields.io/pypi/v/PyBEL.svg
    :target: https://pypi.python.org/pypi/pybel
    :alt: Current version on PyPI

.. |pypi_license| image:: https://img.shields.io/pypi/l/PyBEL.svg
    :target: https://github.com/pybel/pybel/blob/develop/LICENSE
    :alt: Apache 2.0 License

.. |zenodo| image:: https://zenodo.org/badge/68376693.svg
    :target: https://zenodo.org/badge/latestdoi/68376693
