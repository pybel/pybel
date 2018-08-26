# -*- coding: utf-8 -*-

"""Summary functions for edges in BEL graphs."""

from collections import Counter, defaultdict

from ..filters.edge_predicates import edge_has_annotation
from ...constants import ANNOTATIONS, RELATION

__all__ = [
    'iter_annotation_value_pairs',
    'iter_annotation_values',
    'get_annotation_values_by_annotation',
    'get_annotation_values',
    'count_relations',
]


def iter_annotation_value_pairs(graph):
    """Iterate over the key/value pairs, with duplicates, for each annotation used in a BEL graph.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: iter[tuple[str,str]]
    """
    return (
        (key, value)
        for _, _, data in graph.edges(data=True)
        if ANNOTATIONS in data
        for key, values in data[ANNOTATIONS].items()
        for value in values
    )


def iter_annotation_values(graph, annotation):
    """Iterate over all of the values for an annotation used in the graph.

    :param pybel.BELGraph graph: A BEL graph
    :param str annotation: The annotation to grab
    :rtype: iter[str]
    """
    return (
        value
        for _, _, data in graph.edges(data=True)
        if edge_has_annotation(data, annotation)
        for value in data[ANNOTATIONS][annotation]
    )


def _group_dict_set(iterator):
    """Make a dict that accumulates the values for each key in an iterator of doubles.

    :param iter[tuple[A,B]] iterator: An iterator
    :rtype: dict[A,set[B]]
    """
    d = defaultdict(set)
    for key, value in iterator:
        d[key].add(value)
    return dict(d)


def get_annotation_values_by_annotation(graph):
    """Get the set of values for each annotation used in a BEL graph.

    :param pybel.BELGraph graph: A BEL graph
    :return: A dictionary of {annotation key: set of annotation values}
    :rtype: dict[str, set[str]]
    """
    return _group_dict_set(iter_annotation_value_pairs(graph))


def get_annotation_values(graph, annotation):
    """Get all values for the given annotation.

    :param pybel.BELGraph graph: A BEL graph
    :param str annotation: The annotation to summarize
    :return: A set of all annotation values
    :rtype: set[str]
    """
    return set(iter_annotation_values(graph, annotation))


def count_relations(graph):
    """Return a histogram over all relationships in a graph.

    :param pybel.BELGraph graph: A BEL graph
    :return: A Counter from {relation type: frequency}
    :rtype: collections.Counter
    """
    return Counter(
        data[RELATION]
        for _, _, data in graph.edges(data=True)
    )
