PyBEL |zenodo| |build| |coverage| |documentation|
=================================================
`PyBEL <http://pybel.readthedocs.io>`_ is a pure Python package for parsing and handling biological networks encoded in
the `Biological Expression Language <https://biological-expression-language.github.io/>`_
(BEL).

It facilitates data interchange between data formats like `NetworkX <http://networkx.github.io/>`_,
Node-Link JSON, `JGIF <https://github.com/jsongraph/json-graph-specification>`_, CSV, SIF,
`Cytoscape <http://www.cytoscape.org/>`_, `CX <http://www.home.ndexbio.org/data-model/>`_,
`INDRA <https://github.com/sorgerlab/indra>`_, and `GraphDati <https://github.com/graphdati/schemas>`_; database systems
like SQL and `Neo4J <https://neo4j.com>`_; and web services like `NDEx <https://github.com/pybel/pybel2cx>`_,
`BioDati Studio <https://biodati.com/>`_, and `BEL Commons <https://bel-commons-dev.scai.fraunhofer.de>`_. It also
provides exports for analytical tools like `HiPathia <http://hipathia.babelomics.org/>`_,
`Drug2ways <https://github.com/drug2ways/>`_ and `SPIA <https://bioconductor.org/packages/release/bioc/html/SPIA.html>`_;
machine learning tools like `PyKEEN <https://github.com/smartdataanalytics/biokeen>`_ and
`OpenBioLink <https://github.com/OpenBioLink/OpenBioLink#biological-expression-language-bel-writer>`_; and others.

Its companion package, `PyBEL Tools <http://pybel-tools.readthedocs.io/>`_, contains a
suite of functions and pipelines for analyzing the resulting biological networks.

We realize that we have a name conflict with the python wrapper for the cheminformatics package, OpenBabel. If you're
looking for their python wrapper, see `here <https://github.com/openbabel/openbabel/tree/master/scripts/python>`_.

Citation
--------
If you find PyBEL useful for your work, please consider citing:

.. [1] Hoyt, C. T., *et al.* (2017). `PyBEL: a Computational Framework for Biological Expression Language
       <https://doi.org/10.1093/bioinformatics/btx660>`_. *Bioinformatics*, 34(December), 1–2.

Installation |pypi_version| |python_versions| |pypi_license|
------------------------------------------------------------
PyBEL can be installed easily from `PyPI <https://pypi.python.org/pypi/pybel>`_ with the following code in
your favorite shell:

.. code-block:: sh

    $ pip install pybel

or from the latest code on `GitHub <https://github.com/pybel/pybel>`_ with:

.. code-block:: sh

    $ pip install git+https://github.com/pybel/pybel.git

See the `installation documentation <https://pybel.readthedocs.io/en/latest/introduction/installation.html>`_ for more advanced
instructions. Also, check the change log at `CHANGELOG.rst <https://github.com/pybel/pybel/blob/master/CHANGELOG.rst>`_.

Getting Started
---------------
More examples can be found in the `documentation <http://pybel.readthedocs.io>`_ and in the
`PyBEL Notebooks <https://github.com/pybel/pybel-notebooks>`_ repository.

Compiling and Saving a BEL Graph
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This example illustrates how the a BEL document from the `Human Brain Pharmacome
<https://raw.githubusercontent.com/pharmacome/conib>`_ project can be loaded and compiled directly from GitHub.

.. code-block:: python

   >>> import pybel
   >>> url = 'https://raw.githubusercontent.com/pharmacome/conib/master/hbp_knowledge/proteostasis/kim2013.bel'
   >>> graph = pybel.from_bel_script_url(url)

Other functions for loading BEL content from many formats can be found in the
`I/O documentation <https://pybel.readthedocs.io/en/latest/reference/io.html>`_.
Note that PyBEL can handle `BEL 1.0 <https://github.com/OpenBEL/language/raw/master/docs/version_1.0/bel_specification_version_1.0.pdf>`_
and `BEL 2.0+ <https://github.com/OpenBEL/language/raw/master/docs/version_2.0/bel_specification_version_2.0.pdf>`_
simultaneously.

After you have a BEL graph, there are numerous ways to save it. The ``pybel.dump`` function knows
how to output it in many formats based on the file extension you give. For all of the possibilities,
check the `I/O documentation <https://pybel.readthedocs.io/en/latest/reference/io.html>`_.

.. code-block:: python

   >>> import pybel
   >>> graph = ...
   >>> # write as BEL
   >>> pybel.dump(graph, 'my_graph.bel')
   >>> # write as Node-Link JSON for network viewers like D3
   >>> pybel.dump(graph, 'my_graph.bel.nodelink.json')
   >>> # write as GraphDati JSON for BioDati
   >>> pybel.dump(graph, 'my_graph.bel.graphdati.json')
   >>> # write as CX JSON for NDEx
   >>> pybel.dump(graph, 'my_graph.bel.cx.json')
   >>> # write as INDRA JSON for INDRA
   >>> pybel.dump(graph, 'my_graph.indra.json')

Summarizing the Contents of the Graph
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The ``BELGraph`` object has several "dispatches" which are properties that organize its various functionalities.
One is the ``BELGraph.summarize`` dispatch, which allows for printing summaries to the console.

These examples will use the `RAS Model <https://emmaa.indra.bio/dashboard/rasmodel?tab=model>`_  from EMMAA,
so you'll have to be sure to ``pip install indra`` first. The graph can be acquired and summarized with
``BELGraph.summarize.statistics()`` as in:

.. code-block:: python

    >>> import pybel
    >>> graph = pybel.from_emmaa('rasmodel', date='2020-05-29-17-31-58')  # Needs
    >>> graph.summarize.statistics()
    ---------------------  -------------------
    Name                   rasmodel
    Version                2020-05-29-17-31-58
    Number of Nodes        126
    Number of Namespaces   5
    Number of Edges        206
    Number of Annotations  4
    Number of Citations    1
    Number of Authors      0
    Network Density        1.31E-02
    Number of Components   1
    Number of Warnings     0
    ---------------------  -------------------

The number of nodes of each type can be summarized with ``BELGraph.summarize.nodes()`` as in:

.. code-block:: python

    >>> graph.summarize.nodes(examples=False)
    Type (3)        Count
    ------------  -------
    Protein            97
    Complex            27
    Abundance           2


The number of nodes with each namespace can be summarized with ``BELGraph.summarize.namespaces()`` as in:

.. code-block:: python

    >>> graph.summarize.namespaces(examples=False)
    Namespace (4)      Count
    ---------------  -------
    HGNC                  94
    FPLX                   3
    CHEBI                  1
    TEXT                   1

The edges can be summarized with ``BELGraph.summarize.edges()`` as in:

.. code-block:: python

    >>> graph.summarize.edges(examples=False)
    Edge Type (12)                       Count
    ---------------------------------  -------
    Protein increases Protein               64
    Protein hasVariant Protein              48
    Protein partOf Complex                  47
    Complex increases Protein               20
    Protein decreases Protein                9
    Complex directlyIncreases Protein        8
    Protein increases Complex                3
    Abundance partOf Complex                 3
    Protein increases Abundance              1
    Complex partOf Complex                   1
    Protein decreases Abundance              1
    Abundance decreases Protein              1

Grounding the Graph
~~~~~~~~~~~~~~~~~~~
Not all BEL graphs contain both the name and identifier for each entity. Some even use non-standard prefixes
(also called **namespaces** in BEL). Usually, BEL graphs are validated against controlled vocabularies,
so the following demo shows how to add the corresponding identifiers to all nodes.

.. code-block:: python

    from urllib.request import urlretrieve

    url = 'https://github.com/cthoyt/selventa-knowledge/blob/master/selventa_knowledge/large_corpus.bel.nodelink.json.gz'
    urlretrieve(url, 'large_corpus.bel.nodelink.json.gz')

    import pybel
    graph = pybel.load('large_corpus.bel.nodelink.json.gz')

    import pybel.grounding
    grounded_graph = pybel.grounding.ground(graph)

Note: you have to install ``pyobo`` for this to work and be running Python 3.7+.

Displaying a BEL Graph in Jupyter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
After installing ``jinja2`` and ``ipython``, BEL graphs can be displayed in Jupyter notebooks.

.. code-block:: python

   >>> from pybel.examples import sialic_acid_graph
   >>> from pybel.io.jupyter import to_jupyter
   >>> to_jupyter(sialic_acid_graph)

Using the Parser
~~~~~~~~~~~~~~~~
If you don't want to use the ``pybel.BELGraph`` data structure and just want to turn BEL statements into JSON
for your own purposes, you can directly use the ``pybel.parse()`` function.

.. code-block:: python

    >>> import pybel
    >>> pybel.parse('p(hgnc:4617 ! GSK3B) regulates p(hgnc:6893 ! MAPT)')
    {'source': {'function': 'Protein', 'concept': {'namespace': 'hgnc', 'identifier': '4617', 'name': 'GSK3B'}}, 'relation': 'regulates', 'target': {'function': 'Protein', 'concept': {'namespace': 'hgnc', 'identifier': '6893', 'name': 'MAPT'}}}

This functionality can also be exposed through a Flask-based web application with ``python -m pybel.apps.parser`` after
installing ``flask`` with ``pip install flask``. Note that the first run requires about a ~2 second delay to generate
the parser, after which each parse is very fast.

Using the CLI
~~~~~~~~~~~~~
PyBEL also installs a command line interface with the command :code:`pybel` for simple utilities such as data
conversion. In this example, a BEL document is compiled then exported to `GraphML <http://graphml.graphdrawing.org/>`_
for viewing in Cytoscape.

.. code-block:: sh

    $ pybel compile ~/Desktop/example.bel
    $ pybel serialize ~/Desktop/example.bel --graphml ~/Desktop/example.graphml

In Cytoscape, open with :code:`Import > Network > From File`.

Contributing
------------
Contributions, whether filing an issue, making a pull request, or forking, are appreciated. See
`CONTRIBUTING.rst <https://github.com/pybel/pybel/blob/master/CONTRIBUTING.rst>`_ for more information on getting
involved.

Acknowledgements
----------------
Support
~~~~~~~
The development of PyBEL has been supported by several projects/organizations (in alphabetical order):

- `The Cytoscape Consortium <https://cytoscape.org/>`_
- `Enveda Biosciences <https://envedabio.com/>`_
- `Fraunhofer Center for Machine Learning <https://www.cit.fraunhofer.de/de/zentren/maschinelles-lernen.html>`_
- `Fraunhofer Institute for Algorithms and Scientific Computing (SCAI) <https://www.scai.fraunhofer.de>`_
- `Harvard Program in Therapeutic Science - Laboratory of Systems Pharmacology <https://hits.harvard.edu/the-program/laboratory-of-systems-pharmacology>`_
- `University of Bonn <https://www.uni-bonn.de>`_

Funding
~~~~~~~
- DARPA Young Faculty Award W911NF2010255 (PI: Benjamin M. Gyori).
- The `European Union <https://europa.eu>`_, `European Federation of Pharmaceutical Industries and Associations
  (EFPIA) <https://www.efpia.eu/>`_, and `Innovative Medicines Initiative <https://www.imi.europa.eu>`_ Joint
  Undertaking under `AETIONOMY <https://www.aetionomy.eu/>`_ [grant number 115568], resources of which
  are composed of financial contribution from the European Union's Seventh Framework Programme (FP7/2007-2013) and
  EFPIA companies in kind contribution.

Logo
~~~~
The PyBEL `logo <https://github.com/pybel/pybel-art>`_ was designed by `Scott Colby <https://github.com/scolby33>`_.

.. |build| image:: https://github.com/pybel/pybel/workflows/Tests/badge.svg
    :target: https://github.com/pybel/pybel/actions
    :alt: Build Status

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
    :target: https://github.com/pybel/pybel/blob/master/LICENSE
    :alt: MIT License

.. |zenodo| image:: https://zenodo.org/badge/68376693.svg
    :target: https://zenodo.org/badge/latestdoi/68376693
