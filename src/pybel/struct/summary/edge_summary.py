# -*- coding: utf-8 -*-

"""Summary functions for edges in BEL graphs."""

from collections import Counter, defaultdict
from random import choice
from typing import Iterable, Mapping, Set, Tuple

from ..filters.edge_predicates import edge_has_annotation
from ..graph import BELGraph
from ...canonicalize import edge_to_bel
from ...constants import ANNOTATIONS, RELATION
from ...dsl import BaseEntity
from ...language import Entity
from ...utils import CanonicalEdge, canonicalize_edge

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
    'get_metaedge_to_key',
    'iter_sample_metaedges',
]


def iter_annotation_value_pairs(graph: BELGraph) -> Iterable[Tuple[str, Entity]]:
    """Iterate over the key/value pairs, with duplicates, for each annotation used in a BEL graph.

    :param graph: A BEL graph
    """
    return (
        (key, entity)
        for _, _, data in graph.edges(data=True)
        for key, entities in data.get(ANNOTATIONS, {}).items()
        for entity in entities
    )


def iter_annotation_values(graph: BELGraph, annotation: str) -> Iterable[Entity]:
    """Iterate over all of the values for an annotation used in the graph.

    :param graph: A BEL graph
    :param annotation: The annotation to grab
    """
    return (
        entity
        for _, _, data in graph.edges(data=True)
        if edge_has_annotation(data, annotation)
        for entity in data[ANNOTATIONS][annotation]
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


def get_annotation_values_by_annotation(graph: BELGraph) -> Mapping[str, Set[Entity]]:
    """Get the set of values for each annotation used in a BEL graph.

    :param graph: A BEL graph
    :return: A dictionary of {annotation key: set of annotation values}
    """
    return _group_dict_set(iter_annotation_value_pairs(graph))


def get_annotation_values(graph: BELGraph, annotation: str) -> Set[Entity]:
    """Get all values for the given annotation.

    :param graph: A BEL graph
    :param annotation: The annotation to summarize
    :return: A set of all annotation values
    """
    return set(iter_annotation_values(graph, annotation))


def count_relations(graph: BELGraph) -> Counter:
    """Return a histogram over all relationships in a graph.

    :param graph: A BEL graph
    :return: A Counter from {relation type: frequency}
    """
    return Counter(
        data[RELATION]
        for _, _, data in graph.edges(data=True)
    )


def get_unused_annotations(graph: BELGraph) -> Set[str]:
    """Get the set of all annotations that are defined in a graph, but are never used.

    :param graph: A BEL graph
    :return: A set of annotations
    """
    return graph.defined_annotation_keywords - get_annotations(graph)


def get_annotations(graph: BELGraph) -> Set[str]:
    """Get the set of annotations used in the graph.

    :param graph: A BEL graph
    :return: A set of annotation keys
    """
    return set(_annotation_iter_helper(graph))


def count_annotations(graph: BELGraph) -> Counter:
    """Count how many times each annotation is used in the graph.

    :param graph: A BEL graph
    :return: A Counter from {annotation key: frequency}
    """
    return Counter(_annotation_iter_helper(graph))


def _annotation_iter_helper(graph: BELGraph) -> Iterable[str]:
    """Iterate over the annotation keys.

    :param graph: A BEL graph
    """
    return (
        key
        for _, _, data in graph.edges(data=True)
        if ANNOTATIONS in data
        for key in data[ANNOTATIONS]
    )


def get_unused_list_annotation_values(graph: BELGraph) -> Mapping[str, Set[str]]:
    """Get all of the unused values for list annotations.

    :param graph: A BEL graph
    :return: A dictionary of {str annotation: set of str values that aren't used}
    """
    result = {}
    for annotation, values in graph.annotation_list.items():
        unused = values - {e.identifier for e in get_annotation_values(graph, annotation)}
        if unused:
            result[annotation] = unused
    return result


def get_metaedge_to_key(graph: BELGraph) -> Mapping[CanonicalEdge, Set[Tuple[BaseEntity, BaseEntity, str]]]:
    """Get all edge types."""
    rv = defaultdict(set)
    for u, v, k, d in graph.edges(keys=True, data=True):
        rel, u_mod, v_mod = canonicalize_edge(d)
        rv[u.__class__.__name__, u_mod, rel, v.__class__.__name__, v_mod].add((u, v, k))
    return dict(rv)


def iter_sample_metaedges(graph: BELGraph):
    """Iterate sampled metaedges."""
    for k, value in get_metaedge_to_key(graph).items():
        u, v, key = choice(list(value))
        d = graph[u][v][key]
        bel = edge_to_bel(u, v, d, use_identifiers=True)
        yield (u, v, key, d, *k, bel)
