# -*- coding: utf-8 -*-

from ...constants import ANNOTATIONS

__all__ = [
    'strip_annotations',
]


def strip_annotations(graph):
    """Strips all the annotations from a BEL graph

    :param pybel.BELGraph graph: A BEL graph
    """
    for u, v, k in graph.edges_iter(keys=True):
        if ANNOTATIONS in graph.edge[u][v][k]:
            del graph.edge[u][v][k][ANNOTATIONS]
