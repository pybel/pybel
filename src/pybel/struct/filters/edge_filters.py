# -*- coding: utf-8 -*-

"""
Edge Filters
------------

A edge predicate is a function that takes five arguments: a :class:`BELGraph`, a source node tuple, a target node
tuple, a key, and a data dictionary. It returns a boolean representing whether the edge passed the given test.

This module contains a set of default functions for filtering lists of edges and building edge predicate functions.

A general use for an edge predicate is to use the built-in :func:`filter` in code like
:code:`filter(your_edge_predicate, graph.edges_iter(keys=True, data=True))`
"""

from collections import Iterable

from .edge_predicates import keep_edge_permissive

__all__ = [
    'invert_edge_filter',
    'and_edge_predicates',
    'filter_edges',
    'count_passed_edge_filter',
]


def invert_edge_filter(edge_predicate):
    """Builds a filter that is the inverse of the given filter

    :param edge_predicate: An edge filter function (graph, node, node, key, data) -> bool
    :type edge_predicate: types.FunctionType
    :return: An edge filter function
    :rtype: (pybel.BELGraph, tuple, tuple, int) -> bool
    """

    def inverse_filter(graph, u, v, k):
        return not edge_predicate(graph, u, v, k)

    return inverse_filter


def and_edge_predicates(edge_predicates=None):
    """Concatenates multiple edge predicates to a new predicate that requires all predicates to be met.

    :param edge_predicates: a list of predicates (graph, node, node, key, data) -> bool
    :type edge_predicates: types.FunctionType or iter[types.FunctionType]
    :return: A combine filter (graph, node, node, key, data) -> bool
    :rtype: types.FunctionType
    """

    # If no filters are given, then return the trivially permissive filter
    if not edge_predicates:
        return keep_edge_permissive

    # If something that isn't a list or tuple is given, assume it's a function and return it
    if not isinstance(edge_predicates, Iterable):
        return edge_predicates

    edge_predicates = list(edge_predicates)

    # If only one predicate is given, don't bother wrapping it
    if 1 == len(edge_predicates):
        return edge_predicates[0]

    def concatenated_edge_predicate(graph, u, v, k):
        """Passes only for an edge that pass all enclosed predicates

        :param BELGraph graph: A BEL Graph
        :param tuple u: A BEL node
        :param tuple v: A BEL node
        :param int k: The edge key between the given nodes
        :return: If the edge passes all enclosed predicates
        :rtype: bool
        """
        return all(
            edge_predicate(graph, u, v, k)
            for edge_predicate in edge_predicates
        )

    return concatenated_edge_predicate


def filter_edges(graph, edge_predicates=None):
    """Applies a set of filters to the edges iterator of a BEL graph

    :param BELGraph graph: A BEL graph
    :param edge_predicates: A predicate or list of predicates
    :type edge_predicates: types.FunctionType or list[types.FunctionType] or tuple[types.FunctionType]
    :return: An iterable of edges that pass all predicates
    :rtype: iter[tuple,tuple,int]
    """

    # If no predicates are given, return the standard edge iterator
    if not edge_predicates:
        for u, v, k in graph.edges_iter(keys=True):
            yield u, v, k
    else:
        compound_edge_predicate = and_edge_predicates(edge_predicates=edge_predicates)
        for u, v, k in graph.edges_iter(keys=True):
            if compound_edge_predicate(graph, u, v, k):
                yield u, v, k


def count_passed_edge_filter(graph, edge_predicates=None):
    """Returns the number of edges passing a given set of predicates

    :param pybel.BELGraph graph: A BEL graph
    :param edge_predicates: A predicate or list of predicates
    :type edge_predicates: types.FunctionType or list[types.FunctionType] or tuple[types.FunctionType]
    :return: The number of edges passing a given set of predicates
    :rtype: int
    """
    return sum(1 for _ in filter_edges(graph, edge_predicates=edge_predicates))
