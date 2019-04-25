# -*- coding: utf-8 -*-

"""Summary functions for edges in BEL graphs."""

from collections import Counter, defaultdict
from typing import Iterable, Mapping, Set, Tuple

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


def iter_annotation_value_pairs(graph) -> Iterable[Tuple[str, str]]:
    """Iterate over the key/value pairs, with duplicates, for each annotation used in a BEL graph.

    :param pybel.BELGraph graph: A BEL graph
    """
    return (
        (key, value)
        for _, _, data in graph.edges(data=True)
        if ANNOTATIONS in data
        for key, values in data[ANNOTATIONS].items()
        for value in values
    )


def iter_annotation_values(graph, annotation: str) -> Iterable[str]:
    """Iterate over all of the values for an annotation used in the graph.

    :param pybel.BELGraph graph: A BEL graph
    :param str annotation: The annotation to grab
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


def get_annotation_values_by_annotation(graph) -> Mapping[str, Set[str]]:
    """Get the set of values for each annotation used in a BEL graph.

    :param pybel.BELGraph graph: A BEL graph
    :return: A dictionary of {annotation key: set of annotation values}
    """
    return _group_dict_set(iter_annotation_value_pairs(graph))


def get_annotation_values(graph, annotation: str) -> Set[str]:
    """Get all values for the given annotation.

    :param pybel.BELGraph graph: A BEL graph
    :param annotation: The annotation to summarize
    :return: A set of all annotation values
    """
    return set(iter_annotation_values(graph, annotation))


def count_relations(graph) -> Counter:
    """Return a histogram over all relationships in a graph.

    :param pybel.BELGraph graph: A BEL graph
    :return: A Counter from {relation type: frequency}
    """
    return Counter(
        data[RELATION]
        for _, _, data in graph.edges(data=True)
    )


def get_unused_annotations(graph) -> Set[str]:
    """Get the set of all annotations that are defined in a graph, but are never used.

    :param pybel.BELGraph graph: A BEL graph
    :return: A set of annotations
    """
    return graph.defined_annotation_keywords - get_annotations(graph)


def get_annotations(graph) -> Set[str]:
    """Get the set of annotations used in the graph.

    :param pybel.BELGraph graph: A BEL graph
    :return: A set of annotation keys
    """
    return set(_annotation_iter_helper(graph))


def count_annotations(graph) -> Counter:
    """Count how many times each annotation is used in the graph.

    :param pybel.BELGraph graph: A BEL graph
    :return: A Counter from {annotation key: frequency}
    """
    return Counter(_annotation_iter_helper(graph))


def _annotation_iter_helper(graph) -> Iterable[str]:
    """Iterate over the annotation keys.

    :param pybel.BELGraph graph: A BEL graph
    """
    return (
        key
        for _, _, data in graph.edges(data=True)
        if ANNOTATIONS in data
        for key in data[ANNOTATIONS]
    )


def get_unused_list_annotation_values(graph) -> Mapping[str, Set[str]]:
    """Get all of the unused values for list annotations.

    :param pybel.BELGraph graph: A BEL graph
    :return: A dictionary of {str annotation: set of str values that aren't used}
    """
    result = {}
    for annotation, values in graph.annotation_list.items():
        used_values = get_annotation_values(graph, annotation)
        if len(used_values) == len(values):  # all values have been used
            continue
        result[annotation] = set(values) - used_values
    return result
