# -*- coding: utf-8 -*-

"""Utility functions for grouping sub-graphs by citation."""

from collections import defaultdict
from typing import Mapping, Tuple

from ..graph import BELGraph
from ...constants import CITATION, CITATION_DB, CITATION_IDENTIFIER

__all__ = [
    'get_subgraphs_by_citation',
]


def get_subgraphs_by_citation(graph: BELGraph) -> Mapping[Tuple[str, str], BELGraph]:
    """Stratify the graph based on citations.

    :param graph: A BEL graph
    :return: A mapping of each citation db/id to the BEL graph from it.
    """
    rv = defaultdict(graph.child)

    for u, v, key, data in graph.edges(keys=True, data=True):
        if CITATION not in data:
            continue
        dk = data[CITATION][CITATION_DB], data[CITATION][CITATION_IDENTIFIER]

        rv[dk].add_edge(u, v, key=key, **data)

    return dict(rv)
