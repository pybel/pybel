# -*- coding: utf-8 -*-

"""Functions for building node predicates."""

from typing import Any, Callable, Iterable

from .typing import NodePredicate
from ..graph import BELGraph
from ...constants import NAME, NAMESPACE
from ...dsl import BaseEntity
from ...typing import Strings

__all__ = [
    'function_inclusion_filter_builder',
    'data_missing_key_builder',
    'build_node_data_search',
    'build_node_graph_data_search',
    'build_node_key_search',
    'build_node_name_search',
    'namespace_inclusion_builder',
]


def function_inclusion_filter_builder(func: Strings) -> NodePredicate:
    """Build a filter that only passes on nodes of the given function(s).

    :param func: A BEL Function or list/set/tuple of BEL functions
    """
    if isinstance(func, str):
        return _single_function_inclusion_filter_builder(func)

    elif isinstance(func, Iterable):
        return _collection_function_inclusion_builder(func)

    raise TypeError('Invalid type for argument: {}'.format(func))


def _single_function_inclusion_filter_builder(func: str) -> NodePredicate:  # noqa: D202
    """Build a function inclusion filter for a single function."""

    def function_inclusion_filter(_: BELGraph, node: BaseEntity) -> bool:
        """Pass only for a node that has the enclosed function."""
        return node.function == func

    return function_inclusion_filter


def _collection_function_inclusion_builder(funcs: Iterable[str]) -> NodePredicate:
    """Build a function inclusion filter for a collection of functions."""
    funcs = set(funcs)

    if not funcs:
        raise ValueError('can not build function inclusion filter with empty list of functions')

    def functions_inclusion_filter(_: BELGraph, node: BaseEntity) -> bool:
        """Pass only for a node that is one of the enclosed functions."""
        return node.function in funcs

    return functions_inclusion_filter


def data_missing_key_builder(key: str) -> NodePredicate:  # noqa: D202
    """Build a filter that passes only on nodes that don't have the given key in their data dictionary.

    :param str key: A key for the node's data dictionary
    """

    def data_does_not_contain_key(graph: BELGraph, node: BaseEntity) -> bool:
        """Pass only for a node that doesn't contain the enclosed key in its data dictionary."""
        return key not in graph.nodes[node]

    return data_does_not_contain_key


def build_node_data_search(key: str, data_predicate: Callable[[Any], bool]) -> NodePredicate:  # noqa: D202
    """Build a filter for nodes whose associated data with the given key passes the given predicate.

    :param key: The node data dictionary key to check
    :param data_predicate: The filter to apply to the node data dictionary
    """

    def node_data_filter(_: BELGraph, node: BaseEntity) -> bool:
        """Pass if the given node has a given data annotated and passes the contained filter."""
        value = node.get(key)
        return value is not None and data_predicate(value)

    return node_data_filter


def build_node_graph_data_search(key: str, data_predicate: Callable[[Any], bool]):  # noqa: D202
    """Build a function for testing data associated with the node in the graph.

    :param key: The node data dictionary key to check
    :param data_predicate: The filter to apply to the node data dictionary
    """

    def node_data_filter(graph: BELGraph, node: BaseEntity) -> bool:
        """Pass if the given node has a given data annotated and passes the contained filter."""
        value = graph.nodes[node].get(key)
        return value is not None and data_predicate(value)

    return node_data_filter


def build_node_key_search(query, key) -> NodePredicate:
    """Build a node filter for nodes whose values for the given key are superstrings of the query string(s).

    :param query: The query string or strings to check if they're in the node name
    :type query: str or iter[str]
    :param str key: The key for the node data dictionary. Should refer only to entries that have str values
    """
    if isinstance(query, str):
        return build_node_data_search(key, lambda s: query.lower() in s.lower())

    if isinstance(query, Iterable):
        return build_node_data_search(key, lambda s: any(q.lower() in s.lower() for q in query))

    raise TypeError('query is wrong type: %s', query)


def build_node_name_search(query: Strings) -> NodePredicate:
    """Search nodes' names.

    Is a thin wrapper around :func:`build_node_key_search` with :data:`pybel.constants.NAME`

    :param query: The query string or strings to check if they're in the node name
    """
    return build_node_key_search(query=query, key=NAME)


def namespace_inclusion_builder(namespace: Strings) -> NodePredicate:
    """Build a predicate for namespace inclusion."""
    if isinstance(namespace, str):
        def namespace_filter(_: BELGraph, node: BaseEntity) -> bool:
            """Pass only for a node that has the enclosed namespace."""
            return NAMESPACE in node and node[NAMESPACE] == namespace

    elif isinstance(namespace, Iterable):
        namespaces = set(namespace)

        def namespace_filter(_: BELGraph, node: BaseEntity) -> bool:
            """Pass only for a node that has a namespace in the enclosed set."""
            return NAMESPACE in node and node[NAMESPACE] in namespaces

    else:
        raise TypeError('Invalid type for argument: {}'.format(namespace))

    return namespace_filter
