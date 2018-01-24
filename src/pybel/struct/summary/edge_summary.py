# -*- coding: utf-8 -*-

"""This module contains functions that provide summaries of the edges in a graph"""

from ...constants import ANNOTATIONS

__all__ = [
    'iter_annotation_values',
]


def iter_annotation_values(graph):
    """Iterates over the key/value pairs, with duplicates, for each annotation used in a BEL graph

    :param pybel.BELGraph graph: A BEL graph
    :rtype: iter[tuple[str,str]]
    """
    return (
        (key, value)
        for _, _, data in graph.edges_iter(data=True)
        if ANNOTATIONS in data
        for key, values in data[ANNOTATIONS].items()
        for value in values
    )
