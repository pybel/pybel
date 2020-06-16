# -*- coding: utf-8 -*-

"""Utility functions for grouping sub-graphs."""

import warnings

from ..utils import update_metadata

__all__ = [
    'cleanup',
]


def cleanup(graph, subgraphs):
    """Clean up the metadata in the subgraphs.

    :type graph: pybel.BELGraph
    :type subgraphs: dict[Any,pybel.BELGraph]
    """
    warnings.warn('Will be removed before next release', DeprecationWarning)
    for subgraph in subgraphs.values():
        update_metadata(graph, subgraph)
