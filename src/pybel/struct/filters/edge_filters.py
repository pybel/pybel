# -*- coding: utf-8 -*-

"""
Edge Filters
------------

A edge filter is a function that takes five arguments: a :class:`BELGraph`, a source node tuple, a target node
tuple, a key, and a data dictionary. It returns a boolean representing whether the edge passed the given test.

This module contains a set of default functions for filtering lists of edges and building edge filtering functions.

A general use for an edge filter function is to use the built-in :func:`filter` in code like
:code:`filter(your_edge_filter, graph.edges_iter(keys=True, data=True))`
"""

__all__ = [
    'keep_edge_permissive',
    'concatenate_edge_filters',
    'filter_edges',
    'count_passed_edge_filter',
    'filter_provenance_edges',
]


def keep_edge_permissive(graph, u, v, k, d):
    """Passes for all edges

    :param BELGraph graph: A BEL Graph
    :param tuple u: A BEL node
    :param tuple v: A BEL node
    :param int k: The edge key between the given nodes
    :param dict d: The edge data dictionary
    :return: Always returns :code:`True`
    :rtype: bool
    """
    return True


def concatenate_edge_filters(filters):
    """Concatenates multiple edge filters to a new filter that requires all filters to be met.

    :param filters: a list of predicates (graph, node, node, key, data) -> bool
    :type filters: types.FunctionType or list[types.FunctionType] or tuple[types.FunctionType]
    :return: A combine filter (graph, node, node, key, data) -> bool
    :rtype: types.FunctionType
    """

    # If no filters are given, then return the trivially permissive filter
    if not filters:
        return keep_edge_permissive

    # If something that isn't a list or tuple is given, assume it's a function and return it
    if not isinstance(filters, (list, tuple)):
        return filters

    # If only one filter is given, don't bother wrapping it
    if 1 == len(filters):
        return filters[0]

    def concatenated_edge_filter(graph, u, v, k, d):
        """Passes only for an edge that pass all enclosed filters

        :param BELGraph graph: A BEL Graph
        :param tuple u: A BEL node
        :param tuple v: A BEL node
        :param int k: The edge key between the given nodes
        :param dict d: The edge data dictionary
        :return: If the edge passes all enclosed filters
        :rtype: bool
        """
        return all(f(graph, u, v, k, d) for f in filters)

    return concatenated_edge_filter


def filter_edges(graph, filters=None):
    """Applies a set of filters to the edges iterator of a BEL graph

    :param BELGraph graph: A BEL graph
    :param filters: A filter or list of filters
    :type filters: types.FunctionType or list[types.FunctionType] or tuple[types.FunctionType]
    :return: An iterable of edges that pass all filters
    :rtype: iter
    """

    # If no filters are given, return the standard edge iterator
    if not filters:
        for u, v, k, d in graph.edges_iter(keys=True, data=True):
            yield u, v, k, d
    else:
        concatenated_edge_filter = concatenate_edge_filters(filters)
        for u, v, k, d in graph.edges_iter(keys=True, data=True):
            if concatenated_edge_filter(graph, u, v, k, d):
                yield u, v, k, d


def count_passed_edge_filter(graph, filters=None):
    """Returns the number of edges passing a given set of filters

    :param pybel.BELGraph graph: A BEL graph
    :param filters: A filter or list of filters
    :type filters: types.FunctionType or list[types.FunctionType] or tuple[types.FunctionType]
    :return: The number of edges passing a given set of filters
    :rtype: int
    """
    return sum(1 for _ in filter_edges(graph, filters))


def edge_has_provenance(graph, u, v, k, d):
    """Passes for edges with provenance information (i.e. citation and evidence)

    :param BELGraph graph: A BEL Graph
    :param tuple u: A BEL node
    :param tuple v: A BEL node
    :param int k: The edge key between the given nodes
    :param dict d: The edge data dictionary
    :return: If the edge has both a citation and and evidence entry
    :rtype: bool
    """
    return graph.has_edge_citation(u, v, k) and graph.has_edge_evidence(u, v, k)


def filter_provenance_edges(graph):
    """Returns an iterator over edges with citation and evidence

    :param BELGraph graph: A BEL graph
    :return: An iterator over edges with both a citation and evidence
    :rtype: iter[tuple]
    """
    return filter_edges(graph, edge_has_provenance)
