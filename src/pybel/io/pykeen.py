# -*- coding: utf-8 -*-

"""Entry points for PyKEEN."""

import numpy as np

from .gpickle import from_pickle
from .nodelink import from_nodelink_file
from .tsv.api import get_triples
from .web import from_web

__all__ = [
    'get_triples_from_bel',
    'get_triples_from_bel_nodelink',
    'get_triples_from_bel_pickle',
    'get_triples_from_bel_commons',
]


def get_triples_from_bel(path: str) -> np.ndarray:
    """Get triples from a BEL file."""
    from pybel import from_bel_script
    return _from_bel(path, from_bel_script)


def get_triples_from_bel_nodelink(path: str) -> np.ndarray:
    """Get triples from a BEL Node-link JSON file."""
    return _from_bel(path, from_nodelink_file)


def get_triples_from_bel_pickle(path: str) -> np.ndarray:
    """Get triples from a BEL pickle file."""
    return _from_bel(path, from_pickle)


def get_triples_from_bel_commons(network_id: str) -> np.ndarray:
    """Load a BEL document from BEL Commons."""
    return _from_bel(str(network_id), from_web)


def _from_bel(path, bel_importer) -> np.ndarray:
    graph = bel_importer(path)
    triples = get_triples(graph)
    return np.array(triples)
