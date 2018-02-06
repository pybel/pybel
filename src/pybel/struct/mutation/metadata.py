# -*- coding: utf-8 -*-

from ...constants import ANNOTATIONS

__all__ = [
    'strip_annotations',
]


def strip_annotations(graph):
    """Strips all the annotations from a BELGraph

    :type graph: pybel.BELGraph
    """
    for u, v, k in graph.edges(keys=True):
        if ANNOTATIONS in graph.edges[u, v, k]:
            del graph.edges[u, v, k][ANNOTATIONS]
