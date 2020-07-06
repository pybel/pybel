# -*- coding: utf-8 -*-

"""Entry points for PyKEEN.

PyKEEN is a machine learning library for knowledge graph embeddings that supports node clustering,
link prediction, entity disambiguation, question/answering, and other tasks with knowledge graphs.
It provides an interface for registering plugins using Python's entrypoints under the
``pykeen.triples.extension_importer`` and ``pykeen.triples.prefix_importer`` groups. More specific
information about how the PyBEL plugins are loaded into PyKEEN can be found in PyBEL's
`setup.cfg <https://github.com/pybel/pybel/blob/master/setup.cfg>`_ under the ``[options.entry_points]``
header.

The following example shows how you can parse/load the triples from a BEL document with the `*.bel` extension.

.. code-block:: python

    from urllib.request import urlretrieve
    url = 'https://raw.githubusercontent.com/cthoyt/selventa-knowledge/master/selventa_knowledge/small_corpus.bel'
    urlretrieve(url, 'small_corpus.bel')

    # Example 1A: Make triples factory
    from pykeen.triples import TriplesFactory
    tf = TriplesFactory(path='small_corpus.bel')

    # Example 1B: Use directly in the pipeline, which automatically invokes training/testing set stratification
    from pykeen.pipeline import pipeline
    results = pipeline(
        dataset='small_corpus.bel',
        model='TransE',
    )

The same is true for precompiled BEL documents in the node-link format with the `*.bel.nodelink.json` extension and
the pickle format with the `*.bel.pickle` extension.

The following example shows how you can load/parse the triples from a BEL document stored in BEL Commons using the
``bel-commons`` prefix in combination with the network's identifier.

.. code-block:: python

    # Example 2A: Make a triples factory
    from pykeen.triples import TriplesFactory
    # the network's identifier is 528
    tf = TriplesFactory(path='bel-commons:528')

    # Example 1B: Use directly in the pipeline, which automatically invokes training/testing set stratification
    from pykeen.pipeline import pipeline
    results = pipeline(
        dataset='bel-commons:528',
        model='TransR',
    )

Currently, this relies on the default BEL Commons service provider at https://bel-commons-dev.scai.fraunhofer.de,
whose location might change in the future.
"""

import numpy as np

from .bel_commons_client import from_bel_commons
from .gpickle import from_pickle
from .nodelink import from_nodelink_file
from .triples import to_triples

__all__ = [
    'get_triples_from_bel',
    'get_triples_from_bel_nodelink',
    'get_triples_from_bel_pickle',
    'get_triples_from_bel_commons',
]


def get_triples_from_bel(path: str) -> np.ndarray:
    """Get triples from a BEL file by wrapping :func:`pybel.io.tsv.api.get_triples`.

    :param path: the file path to a BEL Script
    :return: A three column array with head, relation, and tail in each row
    """
    from pybel import from_bel_script
    return _from_bel(path, from_bel_script)


def get_triples_from_bel_nodelink(path: str) -> np.ndarray:
    """Get triples from a BEL Node-link JSON file by wrapping :func:`pybel.io.tsv.api.get_triples`.

    :param path: the file path to a BEL Node-link JSON file
    :return: A three column array with head, relation, and tail in each row
    """
    return _from_bel(path, from_nodelink_file)


def get_triples_from_bel_pickle(path: str) -> np.ndarray:
    """Get triples from a BEL pickle file by wrapping :func:`pybel.io.tsv.api.get_triples`.

    :param path: the file path to a BEL pickle file
    :return: A three column array with head, relation, and tail in each row
    """
    return _from_bel(path, from_pickle)


def get_triples_from_bel_commons(network_id: str) -> np.ndarray:
    """Load a BEL document from BEL Commons by wrapping :func:`pybel.io.tsv.api.get_triples`.

    :param network_id: The network identifier for a graph in BEL Commons
    :return: A three column array with head, relation, and tail in each row
    """
    return _from_bel(str(network_id), from_bel_commons)


def _from_bel(path, bel_importer) -> np.ndarray:
    graph = bel_importer(path)
    triples = to_triples(graph)
    return np.array(triples)
