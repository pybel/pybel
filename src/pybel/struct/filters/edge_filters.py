# -*- coding: utf-8 -*-

"""Filter functions for edges in BEL graphs.

A edge predicate is a function that takes five arguments: a :class:`BELGraph`, a source node, a target node, a key,
and a data dictionary. It returns a boolean representing whether the edge passed the given test.

This module contains a set of default functions for filtering lists of edges and building edge predicate functions.

A general use for an edge predicate is to use the built-in :func:`filter` in code like
:code:`filter(your_edge_predicate, graph.edges(keys=True, data=True))`
"""

from typing import Iterable

from .typing import EdgeIterator, EdgePredicate, EdgePredicates
from ..graph import BELGraph
from ...dsl import BaseEntity

__all__ = [
    'invert_edge_predicate',
    'and_edge_predicates',
    'filter_edges',
    'count_passed_edge_filter',
]


def invert_edge_predicate(edge_predicate: EdgePredicate) -> EdgePredicate:  # noqa: D202
    """Build an edge predicate that is the inverse of the given edge predicate."""

    def _inverse_filter(graph, u, v, k):
        return not edge_predicate(graph, u, v, k)

    return _inverse_filter


def and_edge_predicates(edge_predicates: EdgePredicates) -> EdgePredicate:
    """Concatenate multiple edge predicates to a new predicate that requires all predicates to be met."""
    # If something that isn't a list or tuple is given, assume it's a function and return it
    if not isinstance(edge_predicates, Iterable):
        return edge_predicates

    edge_predicates = tuple(edge_predicates)

    # If only one predicate is given, don't bother wrapping it
    if 1 == len(edge_predicates):
        return edge_predicates[0]

    def concatenated_edge_predicate(graph: BELGraph, u: BaseEntity, v: BaseEntity, k: str) -> bool:
        """Pass only for an edge that pass all enclosed predicates.

        :return: If the edge passes all enclosed predicates
        """
        return all(
            edge_predicate(graph, u, v, k)
            for edge_predicate in edge_predicates
        )

    return concatenated_edge_predicate


def filter_edges(graph: BELGraph, edge_predicates: EdgePredicates) -> EdgeIterator:
    """Apply a set of filters to the edges iterator of a BEL graph.

    :return: An iterable of edges that pass all predicates
    """
    compound_edge_predicate = and_edge_predicates(edge_predicates=edge_predicates)
    for u, v, k in graph.edges(keys=True):
        if compound_edge_predicate(graph, u, v, k):
            yield u, v, k


def count_passed_edge_filter(graph: BELGraph, edge_predicates: EdgePredicates) -> int:
    """Return the number of edges passing a given set of predicates."""
    return sum(
        1
        for _ in filter_edges(graph, edge_predicates=edge_predicates)
    )
