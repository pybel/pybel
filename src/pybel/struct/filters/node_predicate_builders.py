# -*- coding: utf-8 -*-

"""Functions for building node predicates."""

from typing import Any, Callable, Iterable, List, Union

from .node_predicates import concatenate_node_predicates, invert_node_predicate
from .typing import NodePredicate
from ..graph import BELGraph
from ...constants import CONCEPT, NAME
from ...dsl import BaseConcept, BaseEntity
from ...typing import Strings

__all__ = [
    'function_inclusion_filter_builder',
    'function_exclusion_filter_builder',
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


def function_exclusion_filter_builder(func: Strings) -> NodePredicate:
    """Build a filter that fails on nodes of the given function(s).

    :param func: A BEL Function or list/set/tuple of BEL functions
    """
    return invert_node_predicate(function_inclusion_filter_builder(func))


def data_missing_key_builder(key: str) -> NodePredicate:  # noqa: D202
    """Build a filter that passes only on nodes that don't have the given key in their data dictionary.

    :param str key: A key for the node's data dictionary
    """

    def data_does_not_contain_key(graph: BELGraph, node: BaseEntity) -> bool:
        """Pass only for a node that doesn't contain the enclosed key in its data dictionary."""
        return key not in graph.nodes[node]

    return data_does_not_contain_key


def build_node_data_search(  # noqa: D202
    key: Union[str, List[str]],
    data_predicate: Callable[[Any], bool],
) -> NodePredicate:
    """Build a filter for nodes whose associated data with the given key passes the given predicate.

    :param key: The node data dictionary key to check
    :param data_predicate: The filter to apply to the node data dictionary
    """
    if isinstance(key, list):
        _getter = _get_multi_value
    else:
        _getter = _get_single_value

    def node_data_filter(_: BELGraph, node: BaseEntity) -> bool:
        """Pass if the given node has a given data annotated and passes the contained filter."""
        value = _getter(node, key)
        return value is not None and data_predicate(value)

    return node_data_filter


def build_node_graph_data_search(  # noqa: D202
    key: Union[str, List[str]],
    data_predicate: Callable[[Any], bool],
) -> NodePredicate:
    """Build a function for testing data associated with the node in the graph.

    :param key: The node data dictionary key to check
    :param data_predicate: The filter to apply to the node data dictionary
    """
    if isinstance(key, tuple):
        _getter = _get_multi_value
    else:
        _getter = _get_single_value

    def node_data_filter(graph: BELGraph, node: BaseEntity) -> bool:
        """Pass if the given node has a given data annotated and passes the contained filter."""
        value = _getter(graph.nodes[node], key)
        return value is not None and data_predicate(value)

    return node_data_filter


def _get_multi_value(d, keys):
    value = d.get(keys[0])
    for key in keys[1:]:
        if value is None:
            return
        value = value.get(key)
    return value


def _get_single_value(d, key):
    return d.get(key)


def build_node_key_search(
    query: Strings,
    key: Union[str, List[str]],
) -> NodePredicate:
    """Build a node filter for nodes whose values for the given key are superstrings of the query string(s).

    :param query: The query string or strings to check if they're in the node name
    :param key: The key for the node data dictionary. Should refer only to entries that have str values
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
    return build_node_key_search(query=query, key=[CONCEPT, NAME])


def namespace_inclusion_builder(namespace: Strings) -> NodePredicate:
    """Build a predicate for namespace inclusion."""
    if isinstance(namespace, str):
        def namespace_filter(_: BELGraph, node: BaseEntity) -> bool:
            """Pass only for a node that has the enclosed namespace."""
            return isinstance(node, BaseConcept) and node.namespace == namespace

    elif isinstance(namespace, Iterable):
        namespaces = set(namespace)

        def namespace_filter(_: BELGraph, node: BaseEntity) -> bool:
            """Pass only for a node that has a namespace in the enclosed set."""
            return isinstance(node, BaseConcept) and node.namespace in namespaces

    else:
        raise TypeError('Invalid type for argument: {}'.format(namespace))

    return namespace_filter
