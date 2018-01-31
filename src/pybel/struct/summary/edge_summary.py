# -*- coding: utf-8 -*-

"""This module contains functions that provide summaries of the edges in a graph"""

from collections import defaultdict

from ...constants import ANNOTATIONS

__all__ = [
    'iter_annotation_values',
    'get_annotation_values_by_annotation',
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


def _group_dict_set(iterator):
    """Makes a dict that accumulates the values for each key in an iterator of doubles

    :param iter[tuple[A,B]] iterator: An iterator
    :rtype: dict[A,set[B]]
    """
    d = defaultdict(set)
    for key, value in iterator:
        d[key].add(value)
    return dict(d)


def get_annotation_values_by_annotation(graph):
    """Gets the set of values for each annotation used in a BEL graph

    :param pybel.BELGraph graph: A BEL graph
    :return: A dictionary of {annotation key: set of annotation values}
    :rtype: dict[str, set[str]]
    """
    return _group_dict_set(iter_annotation_values(graph))
