# -*- coding: utf-8 -*-

"""Utility functions for grouping sub-graphs by citation."""

from collections import defaultdict

from .utils import cleanup
from ...constants import CITATION, CITATION_REFERENCE, CITATION_TYPE

__all__ = [
    'get_subgraphs_by_citation',
]


def get_subgraphs_by_citation(graph):
    """Stratify the graph based on citations.

    :type graph: pybel.BELGraph
    :rtype: dict[tuple[str,str],pybel.BELGraph]
    """
    rv = defaultdict(graph.fresh_copy)

    for u, v, key, data in graph.edges(keys=True, data=True):
        if CITATION not in data:
            continue
        dk = data[CITATION][CITATION_TYPE], data[CITATION][CITATION_REFERENCE]

        rv[dk].add_edge(u, v, key=key, **data)

    cleanup(graph, rv)

    return dict(rv)
