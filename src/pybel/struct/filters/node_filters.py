# -*- coding: utf-8 -*-

"""
Node Filters
------------

A node filter is a function that takes two arguments: a :class:`BELGraph` and a node tuple. It returns a boolean
representing whether the node passed the given test.

This module contains a set of default functions for filtering lists of nodes and building node filtering functions.

A general use for a node filter function is to use the built-in :func:`filter` in code like
:code:`filter(your_node_filter, graph.nodes_iter())`
"""

from collections import Iterable

__all__ = [
    'concatenate_node_filters',
    'filter_nodes',
    'get_nodes',
    'count_passed_node_filter',
]


def concatenate_node_filters(node_filters=None):
    """Concatenates multiple node filters to a new filter that requires all filters to be met

    :param node_filters: A predicate or list of predicates (graph, node) -> bool
    :type node_filters: types.FunctionType or iter[types.FunctionType]
    :return: A combine filter (graph, node) -> bool
    :rtype: types.FunctionType

    Example usage:

    >>> from pybel.constants import GENE, PROTEIN, PATHOLOGY
    >>> path_filter = function_exclusion_filter_builder(PATHOLOGY)
    >>> app_filter = node_exclusion_filter_builder([(PROTEIN, 'HGNC', 'APP'), (GENE, 'HGNC', 'APP')])
    >>> my_filter = concatenate_node_filters([path_filter, app_filter])
    """
    # If no filters are given, then return the trivially permissive filter
    if not node_filters:
        return lambda graph, node: True

    # If a filter outside a list is given, just return it
    if not isinstance(node_filters, Iterable):
        return node_filters

    node_filters = list(node_filters)

    # If only one filter is given, don't bother wrapping it
    if 1 == len(node_filters):
        return node_filters[0]

    def concatenated_node_filter(graph, node):
        """Passes only for a nodes that pass all enclosed filters

        :param BELGraph graph: A BEL Graph
        :param tuple node: A BEL node
        :return: If the node passes all enclosed filters
        :rtype: bool
        """
        return all(
            node_filter(graph, node)
            for node_filter in node_filters
        )

    return concatenated_node_filter


def filter_nodes(graph, node_filters=None):
    """Applies a set of filters to the nodes iterator of a BEL graph

    :param BELGraph graph: A BEL graph
    :param node_filters: A node filter or list/tuple of node filters
    :type node_filters: types.FunctionType or iter[types.FunctionType]
    :return: An iterable of nodes that pass all filters
    :rtype: iter
    """

    # If no filters are given, return the standard node iterator
    if not node_filters:
        for node in graph:
            yield node
    else:
        concatenated_filter = concatenate_node_filters(node_filters=node_filters)
        for node in graph:
            if concatenated_filter(graph, node):
                yield node


def get_nodes(graph, node_filters=None):
    """Gets the set of all nodes that pass the filters

    :param BELGraph graph: A BEL graph
    :param node_filters: A node filter or list/tuple of node filters
    :type node_filters: types.FunctionType or iter[types.FunctionType]
    :return: The set of nodes passing the filters
    :rtype: set[tuple]
    """
    return set(filter_nodes(graph, node_filters))


def count_passed_node_filter(graph, node_filters=None):
    """Counts how many nodes pass a given set of filters

    :param pybel.BELGraph graph: A BEL graph
    :param node_filters: A node filter or list/tuple of node filters
    :type node_filters: types.FunctionType or iter[types.FunctionType]
    :return: The number of nodes passing the given set of filters
    :rtype: int
    """
    return sum(1 for _ in filter_nodes(graph, node_filters=node_filters))
