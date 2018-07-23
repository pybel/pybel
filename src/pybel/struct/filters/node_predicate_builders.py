# -*- coding: utf-8 -*-

"""Functions for building node predicates."""

from collections import Iterable

from six import string_types

from ...constants import FUNCTION, NAME

__all__ = [
    'function_inclusion_filter_builder',
    'data_missing_key_builder',
    'build_node_data_search',
    'build_node_key_search',
    'build_node_name_search',
]


def _single_function_inclusion_filter_builder(func):
    def function_inclusion_filter(graph, node):
        """Passes only for a node that has the enclosed function

        :param BELGraph graph: A BEL Graph
        :param tuple node: A BEL node
        :return: If the node doesn't have the enclosed function
        :rtype: bool
        """
        return graph.node[node][FUNCTION] == func

    return function_inclusion_filter


def _collection_function_inclusion_builder(funcs):
    funcs = set(funcs)

    if not funcs:
        raise ValueError('can not build function inclusion filter with empty list of functions')

    def functions_inclusion_filter(graph, node):
        """Passes only for a node that is one of the enclosed functions

        :param BELGraph graph: A BEL Graph
        :param tuple node: A BEL node
        :return: If the node doesn't have the enclosed functions
        :rtype: bool
        """
        return graph.node[node][FUNCTION] in funcs

    return functions_inclusion_filter


def function_inclusion_filter_builder(func):
    """Build a filter that only passes on nodes of the given function(s).

    :param func: A BEL Function or list/set/tuple of BEL functions
    :type func: str or iter[str]
    :return: A node filter (graph, node) -> bool
    :rtype: (pybel.BELGraph, tuple) -> bool
    """
    if isinstance(func, string_types):
        return _single_function_inclusion_filter_builder(func)

    elif isinstance(func, Iterable):
        return _collection_function_inclusion_builder(func)

    raise TypeError('Invalid type for argument: {}'.format(func))


def data_missing_key_builder(key):
    """Build a filter that passes only on nodes that don't have the given key in their data dictionary.

    :param str key: A key for the node's data dictionary
    :return: A node filter (graph, node) -> bool
    :rtype: (pybel.BELGraph, tuple) -> bool
    """

    def data_does_not_contain_key(graph, node):
        """Pass only for a node that doesn't contain the enclosed key in its data dictionary.

        :param pybel.BELGraph graph: A BEL Graph
        :param tuple node: A BEL node
        :return: If the node doesn't contain the enclosed key in its data dictionary
        :rtype: bool
        """
        return key not in graph.node[node]

    return data_does_not_contain_key


def build_node_data_search(key, data_predicate):
    """Pass for nodes who have the given key in their data dictionaries and whose associated values pass the given
    filter function.

    :param str key: The node data dictionary key to check
    :param data_predicate: The filter to apply to the node data dictionary
    :type data_predicate: (Any) -> bool
    :return: A node predicate
    :rtype: (pybel.BELGraph, tuple) -> bool
    """

    def node_data_filter(graph, node):
        """Pass if the given node has a given data annotated and passes the contained filter.

        :type graph: pybel.BELGraph
        :type node: tuple
        :return: If the node has the contained key in its data dictionary and passes the contained filter
        :rtype: bool
        """
        data = graph.node[node]
        return key in data and data_predicate(data[key])

    return node_data_filter


def build_node_key_search(query, key):
    """Build a node filter that only passes for nodes whose values for the given key are superstrings of the query
    string(s).

    :param query: The query string or strings to check if they're in the node name
    :type query: str or iter[str]
    :param str key: The key for the node data dictionary. Should refer only to entries that have str values
    :return: A node predicate
    :rtype: (pybel.BELGraph, tuple) -> bool
    """
    if isinstance(query, string_types):
        return build_node_data_search(key, lambda s: query.lower() in s.lower())

    if isinstance(query, Iterable):
        return build_node_data_search(key, lambda s: any(q.lower() in s.lower() for q in query))

    raise TypeError('query is wrong type: %s', query)


def build_node_name_search(query):
    """Search nodes' names.

    Is a thin wrapper around :func:`build_node_key_search` with :data:`pybel.constants.NAME`

    :param query: The query string or strings to check if they're in the node name
    :type query: str or iter[str]
    :return: A node predicate
    :rtype: (pybel.BELGraph, tuple) -> bool
    """
    return build_node_key_search(query=query, key=NAME)
