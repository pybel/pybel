<p align="center">
  <img src="https://github.com/pybel/pybel/raw/main/docs/source/logo.png" height="150">
</p>

<h1 align="center">
  PyBEL
</h1>

<p align="center">
    <a href="https://github.com/pybel/pybel/actions/workflows/tests.yml">
        <img alt="Tests" src="https://github.com/pybel/pybel/actions/workflows/tests.yml/badge.svg" /></a>
    <a href="https://pypi.org/project/pybel">
        <img alt="PyPI" src="https://img.shields.io/pypi/v/pybel" /></a>
    <a href="https://pypi.org/project/pybel">
        <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/pybel" /></a>
    <a href="https://github.com/pybel/pybel/blob/main/LICENSE">
        <img alt="PyPI - License" src="https://img.shields.io/pypi/l/pybel" /></a>
    <a href='https://pybel.readthedocs.io/en/latest/?badge=latest'>
        <img src='https://readthedocs.org/projects/pybel/badge/?version=latest' alt='Documentation Status' /></a>
    <a href="https://codecov.io/gh/pybel/pybel/branch/main">
        <img src="https://codecov.io/gh/pybel/pybel/branch/main/graph/badge.svg" alt="Codecov status" /></a>  
    <a href="https://github.com/cthoyt/cookiecutter-python-package">
        <img alt="Cookiecutter template from @cthoyt" src="https://img.shields.io/badge/Cookiecutter-snekpack-blue" /></a>
    <a href="https://github.com/astral-sh/ruff">
        <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff" style="max-width:100%;"></a>
    <a href="https://github.com/pybel/pybel/blob/main/.github/CODE_OF_CONDUCT.md">
        <img src="https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg" alt="Contributor Covenant"/></a>
    <a href="https://doi.org/10.5281/zenodo.68376693">
        <img src="https://zenodo.org/badge/DOI/10.5281/zenodo.68376693.svg" alt="DOI"></a>
</p>

Parsing, validation, compilation, and data exchange of Biological Expression
Language (BEL).

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

## 💪 Getting Started

More examples can be found in the `documentation <http://pybel.readthedocs.io>`_ and in the
`PyBEL Notebooks <https://github.com/pybel/pybel-notebooks>`_ repository.

### Compiling and Saving a BEL Graph

This example illustrates how a BEL document from the `Human Brain Pharmacome
<https://raw.githubusercontent.com/pharmacome/conib>`_ project can be loaded and compiled directly from GitHub.

```python
import pybel
url = 'https://raw.githubusercontent.com/pharmacome/conib/master/hbp_knowledge/proteostasis/kim2013.bel'
graph = pybel.from_bel_script_url(url)
```

Other functions for loading BEL content from many formats can be found in the
[I/O documentation](https://pybel.readthedocs.io/en/latest/reference/io.html).
Note that PyBEL can handle `BEL 1.0 <https://github.com/OpenBEL/language/raw/master/docs/version_1.0/bel_specification_version_1.0.pdf>`_
and `BEL 2.0+ <https://github.com/OpenBEL/language/raw/master/docs/version_2.0/bel_specification_version_2.0.pdf>`_
simultaneously.

After you have a BEL graph, there are numerous ways to save it. The ``pybel.dump`` function knows
how to output it in many formats based on the file extension you give. For all of the possibilities,
check the `I/O documentation <https://pybel.readthedocs.io/en/latest/reference/io.html>`_.

```python
import pybel
graph = ...
# write as BEL
pybel.dump(graph, 'my_graph.bel')
# write as Node-Link JSON for network viewers like D3
pybel.dump(graph, 'my_graph.bel.nodelink.json')
# write as GraphDati JSON for BioDati
pybel.dump(graph, 'my_graph.bel.graphdati.json')
# write as CX JSON for NDEx
pybel.dump(graph, 'my_graph.bel.cx.json')
# write as INDRA JSON for INDRA
pybel.dump(graph, 'my_graph.indra.json')
```

### Summarizing the Contents of the Graph

The ``BELGraph`` object has several "dispatches" which are properties that organize its various functionalities.
One is the ``BELGraph.summarize`` dispatch, which allows for printing summaries to the console.

These examples will use the `RAS Model <https://emmaa.indra.bio/dashboard/rasmodel?tab=model>`_  from EMMAA,
so you'll have to be sure to ``pip install indra`` first. The graph can be acquired and summarized with
``BELGraph.summarize.statistics()`` as in:

```python
import pybel
graph = pybel.from_emmaa('rasmodel', date='2020-05-29-17-31-58')  # Needs
graph.summarize.statistics()
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
```

The number of nodes of each type can be summarized with ``BELGraph.summarize.nodes()`` as in:

```python
>>> graph.summarize.nodes(examples=False)
Type (3)        Count
------------  -------
Protein            97
Complex            27
Abundance           2
```

The number of nodes with each namespace can be summarized with ``BELGraph.summarize.namespaces()`` as in:

```python
>>> graph.summarize.namespaces(examples=False)
Namespace (4)      Count
---------------  -------
HGNC                  94
FPLX                   3
CHEBI                  1
TEXT                   1
```

The edges can be summarized with ``BELGraph.summarize.edges()`` as in:

```python
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
```

### Grounding the Graph

Not all BEL graphs contain both the name and identifier for each entity. Some even use non-standard prefixes
(also called **namespaces** in BEL). Usually, BEL graphs are validated against controlled vocabularies,
so the following demo shows how to add the corresponding identifiers to all nodes.

```python
from urllib.request import urlretrieve

url = 'https://github.com/cthoyt/selventa-knowledge/blob/master/selventa_knowledge/large_corpus.bel.nodelink.json.gz'
urlretrieve(url, 'large_corpus.bel.nodelink.json.gz')

import pybel
graph = pybel.load('large_corpus.bel.nodelink.json.gz')

import pybel.grounding
grounded_graph = pybel.grounding.ground(graph)
```

Note: you have to install ``pyobo`` for this to work and be running Python 3.7+.

### Displaying a BEL Graph in Jupyter

After installing ``jinja2`` and ``ipython``, BEL graphs can be displayed in Jupyter notebooks.

```python
from pybel.examples import sialic_acid_graph
from pybel.io.jupyter import to_jupyter
to_jupyter(sialic_acid_graph)
```

### Using the Parser

If you don't want to use the ``pybel.BELGraph`` data structure and just want to turn BEL statements into JSON
for your own purposes, you can directly use the ``pybel.parse()`` function.

```python
import pybel
pybel.parse('p(hgnc:4617 ! GSK3B) regulates p(hgnc:6893 ! MAPT)')
# {'source': {'function': 'Protein', 'concept': {'namespace': 'hgnc', 'identifier': '4617', 'name': 'GSK3B'}}, 'relation': 'regulates', 'target': {'function': 'Protein', 'concept': {'namespace': 'hgnc', 'identifier': '6893', 'name': 'MAPT'}}}
```

This functionality can also be exposed through a Flask-based web application with ``python -m pybel.apps.parser`` after
installing ``flask`` with ``pip install flask``. Note that the first run requires about a ~2 second delay to generate
the parser, after which each parse is very fast.


### Command Line Interface

The `pybel` command line tool is automatically installed. It can be used from
the console with the `--help` flag to show all subcommands:

```console
$ pybel --help
```

PyBEL also installs a command line interface with the command :code:`pybel` for simple utilities such as data
conversion. In this example, a BEL document is compiled then exported to `GraphML <http://graphml.graphdrawing.org/>`_
for viewing in Cytoscape.

```console
$ pybel compile ~/Desktop/example.bel
$ pybel serialize ~/Desktop/example.bel --graphml ~/Desktop/example.graphml
```

In Cytoscape, open with :code:`Import > Network > From File`.


## 🚀 Installation

The most recent release can be installed from
[PyPI](https://pypi.org/project/pybel/) with uv:

```console
$ uv pip install pybel
```

or with pip:

```console
$ python3 -m pip install pybel
```

The most recent code and data can be installed directly from GitHub with uv:

```console
$ uv pip install git+https://github.com/pybel/pybel.git
```

or with pip:

```console
$ python3 -m pip install git+https://github.com/pybel/pybel.git
```

## 👐 Contributing

Contributions, whether filing an issue, making a pull request, or forking, are
appreciated. See
[CONTRIBUTING.md](https://github.com/pybel/pybel/blob/main/.github/CONTRIBUTING.md)
for more information on getting involved.

## 👋 Attribution

### ⚖️ License

The code in this package is licensed under the MIT License.

### 📖 Citation

Hoyt, C. T., *et al.* (2017). [PyBEL: a Computational Framework for Biological Expression Language](https://doi.org/10.1093/bioinformatics/btx660). *Bioinformatics*, 34(December), 1–2.

### 🎁 Support

This project has been supported by the following organizations (in alphabetical order):

- [Biopragmatics Lab](https://biopragmatics.github.io)
- [The Cytoscape Consortium](https://cytoscape.org/)
- [Enveda Biosciences](https://envedabio.com/)
- [Fraunhofer Center for Machine Learning](https://www.cit.fraunhofer.de/de/zentren/maschinelles-lernen.html)
- [Fraunhofer Institute for Algorithms and Scientific Computing (SCAI)](https://www.scai.fraunhofer.de)
- [Harvard Program in Therapeutic Science - Laboratory of Systems Pharmacology](https://hits.harvard.edu/the-program/laboratory-of-systems-pharmacology)
- [University of Bonn](https://www.uni-bonn.de)

The PyBEL [logo](https://github.com/pybel/pybel-art) was designed by [Scott Colby](https://github.com/scolby33).

### 💰 Funding

This project has been supported by the following grants:

| Funding Body  | Program                                                      | Grant Number |
|---------------|--------------------------------------------------------------|--------------|
| Funder        | [Grant Name (GRANT-ACRONYM)](https://example.com/grant-link) | ABCXYZ       |


- DARPA Young Faculty Award W911NF2010255 (PI: Benjamin M. Gyori).
- The [European Union](https://europa.eu), [European Federation of Pharmaceutical Industries and Associations
  (EFPIA)](https://www.efpia.eu/), and [Innovative Medicines Initiative](https://www.imi.europa.eu) Joint
  Undertaking under [AETIONOMY](https://www.aetionomy.eu/) [grant number 115568], resources of which
  are composed of financial contribution from the European Union's Seventh Framework Programme (FP7/2007-2013) and
  EFPIA companies in kind contribution.

### 🍪 Cookiecutter

This package was created with
[@audreyfeldroy](https://github.com/audreyfeldroy)'s
[cookiecutter](https://github.com/cookiecutter/cookiecutter) package using
[@cthoyt](https://github.com/cthoyt)'s
[cookiecutter-snekpack](https://github.com/cthoyt/cookiecutter-snekpack)
template.

## 🛠️ For Developers

<details>
  <summary>See developer instructions</summary>

The final section of the README is for if you want to get involved by making a
code contribution.

### Development Installation

To install in development mode, use the following:

```console
$ git clone git+https://github.com/pybel/pybel.git
$ cd pybel
$ uv pip install -e .
```

Alternatively, install using pip:

```console
$ python3 -m pip install -e .
```

### Pre-commit

You can optionally use [pre-commit](https://pre-commit.com) to automate running
key code quality checks on each commit. Enable it with:

```console
$ uvx pre-commit install
```

Or using `pip`:

```console
$ pip install pre-commit
$ pre-commit install
```

### 🥼 Testing

After cloning the repository and installing `tox` with
`uv tool install tox --with tox-uv` or `python3 -m pip install tox tox-uv`, the
unit tests in the `tests/` folder can be run reproducibly with:

```console
$ tox -e py
```

Additionally, these tests are automatically re-run with each commit in a
[GitHub Action](https://github.com/pybel/pybel/actions?query=workflow%3ATests).

### 📖 Building the Documentation

The documentation can be built locally using the following:

```console
$ git clone git+https://github.com/pybel/pybel.git
$ cd pybel
$ tox -e docs
$ open docs/build/html/index.html
```

The documentation automatically installs the package as well as the `docs` extra
specified in the [`pyproject.toml`](pyproject.toml). `sphinx` plugins like
`texext` can be added there. Additionally, they need to be added to the
`extensions` list in [`docs/source/conf.py`](docs/source/conf.py).

The documentation can be deployed to [ReadTheDocs](https://readthedocs.io) using
[this guide](https://docs.readthedocs.io/en/stable/intro/import-guide.html). The
[`.readthedocs.yml`](.readthedocs.yml) YAML file contains all the configuration
you'll need. You can also set up continuous integration on GitHub to check not
only that Sphinx can build the documentation in an isolated environment (i.e.,
with `tox -e docs-test`) but also that
[ReadTheDocs can build it too](https://docs.readthedocs.io/en/stable/pull-requests.html).

</details>

## 🧑‍💻 For Maintainers

<details>
  <summary>See maintainer instructions</summary>

### Initial Configuration

#### Configuring ReadTheDocs

[ReadTheDocs](https://readthedocs.org) is an external documentation hosting
service that integrates with GitHub's CI/CD. Do the following for each
repository:

1. Log in to ReadTheDocs with your GitHub account to install the integration at
   https://readthedocs.org/accounts/login/?next=/dashboard/
2. Import your project by navigating to https://readthedocs.org/dashboard/import
   then clicking the plus icon next to your repository
3. You can rename the repository on the next screen using a more stylized name
   (i.e., with spaces and capital letters)
4. Click next, and you're good to go!

#### Configuring Archival on Zenodo

[Zenodo](https://zenodo.org) is a long-term archival system that assigns a DOI
to each release of your package. Do the following for each repository:

1. Log in to Zenodo via GitHub with this link:
   https://zenodo.org/oauth/login/github/?next=%2F. This brings you to a page
   that lists all of your organizations and asks you to approve installing the
   Zenodo app on GitHub. Click "grant" next to any organizations you want to
   enable the integration for, then click the big green "approve" button. This
   step only needs to be done once.
2. Navigate to https://zenodo.org/account/settings/github/, which lists all of
   your GitHub repositories (both in your username and any organizations you
   enabled). Click the on/off toggle for any relevant repositories. When you
   make a new repository, you'll have to come back to this

After these steps, you're ready to go! After you make "release" on GitHub (steps
for this are below), you can navigate to
https://zenodo.org/account/settings/github/repository/pybel/pybel to see the DOI
for the release and link to the Zenodo record for it.

#### Registering with the Python Package Index (PyPI)

The [Python Package Index (PyPI)](https://pypi.org) hosts packages so they can
be easily installed with `pip`, `uv`, and equivalent tools.

1. Register for an account [here](https://pypi.org/account/register)
2. Navigate to https://pypi.org/manage/account and make sure you have verified
   your email address. A verification email might not have been sent by default,
   so you might have to click the "options" dropdown next to your address to get
   to the "re-send verification email" button
3. 2-Factor authentication is required for PyPI since the end of 2023 (see this
   [blog post from PyPI](https://blog.pypi.org/posts/2023-05-25-securing-pypi-with-2fa/)).
   This means you have to first issue account recovery codes, then set up
   2-factor authentication
4. Issue an API token from https://pypi.org/manage/account/token

This only needs to be done once per developer.

#### Configuring your machine's connection to PyPI

This needs to be done once per machine.

```console
$ uv tool install keyring
$ keyring set https://upload.pypi.org/legacy/ __token__
$ keyring set https://test.pypi.org/legacy/ __token__
```

Note that this deprecates previous workflows using `.pypirc`.

### 📦 Making a Release

#### Uploading to PyPI

After installing the package in development mode and installing `tox` with
`uv tool install tox --with tox-uv` or `python3 -m pip install tox tox-uv`, run
the following from the console:

```console
$ tox -e finish
```

This script does the following:

1. Uses [bump-my-version](https://github.com/callowayproject/bump-my-version) to
   switch the version number in the `pyproject.toml`,`CITATION.cff`,
   `src/pybel/version.py`, and [`docs/source/conf.py`](docs/source/conf.py) to
   not have the `-dev` suffix
2. Packages the code in both a tar archive and a wheel using
   [`uv build`](https://docs.astral.sh/uv/guides/publish/#building-your-package)
3. Uploads to PyPI using
   [`uv publish`](https://docs.astral.sh/uv/guides/publish/#publishing-your-package).
4. Push to GitHub. You'll need to make a release going with the commit where the
   version was bumped.
5. Bump the version to the next patch. If you made big changes and want to bump
   the version by minor, you can use `tox -e bumpversion -- minor` after.

#### Releasing on GitHub

1. Navigate to https://github.com/pybel/pybel/releases/new to draft a new
   release
2. Click the "Choose a Tag" dropdown and select the tag corresponding to the
   release you just made
3. Click the "Generate Release Notes" button to get a quick outline of recent
   changes. Modify the title and description as you see fit
4. Click the big green "Publish Release" button

This will trigger Zenodo to assign a DOI to your release as well.

### Updating Package Boilerplate

This project uses `cruft` to keep boilerplate (i.e., configuration, contribution
guidelines, documentation configuration) up-to-date with the upstream
cookiecutter package. Install cruft with either `uv tool install cruft` or
`python3 -m pip install cruft` then run:

```console
$ cruft update
```

More info on Cruft's update command is available
[here](https://github.com/cruft/cruft?tab=readme-ov-file#updating-a-project).

</details>
