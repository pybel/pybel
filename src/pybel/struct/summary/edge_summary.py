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
    'get_annotations',
    'count_annotations',
    'get_unused_annotations',
    'get_unused_list_annotation_values',
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


def get_unused_annotations(graph):
    """Get the set of all annotations that are defined in a graph, but are never used.

    :param pybel.BELGraph graph: A BEL graph
    :return: A set of annotations
    :rtype: set[str]
    """
    return graph.defined_annotation_keywords - get_annotations(graph)


def get_annotations(graph):
    """Get the set of annotations used in the graph.

    :param pybel.BELGraph graph: A BEL graph
    :return: A set of annotation keys
    :rtype: set[str]
    """
    return set(_annotation_iter_helper(graph))


def count_annotations(graph):
    """Count how many times each annotation is used in the graph.

    :param pybel.BELGraph graph: A BEL graph
    :return: A Counter from {annotation key: frequency}
    :rtype: collections.Counter
    """
    return Counter(_annotation_iter_helper(graph))


def _annotation_iter_helper(graph):
    """Iterate over the annotation keys.

    :type graph: pybel.BELGraph
    :rtype: iter[str]
    """
    return (
        key
        for _, _, data in graph.edges(data=True)
        if ANNOTATIONS in data
        for key in data[ANNOTATIONS]
    )


def get_unused_list_annotation_values(graph):
    """Get all of the unused values for list annotations.

    :param pybel.BELGraph graph: A BEL graph
    :return: A dictionary of {str annotation: set of str values that aren't used}
    :rtype: dict[str,set[str]]
    """
    result = {}
    for annotation, values in graph.annotation_list.items():
        used_values = get_annotation_values(graph, annotation)
        if len(used_values) == len(values):  # all values have been used
            continue
        result[annotation] = set(values) - used_values
    return result
