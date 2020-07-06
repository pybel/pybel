# -*- coding: utf-8 -*-

"""Filter functions for nodes in BEL graphs.

A node predicate is a function that takes two arguments: a :class:`BELGraph` and a node. It returns a boolean
representing whether the node passed the given test.

This module contains a set of default functions for filtering lists of nodes and building node predicates.

A general use for a node predicate is to use the built-in :func:`filter` in code like
:code:`filter(your_node_predicate, graph)`
"""

from typing import Iterable, Set

from .node_predicate_builders import function_inclusion_filter_builder, namespace_inclusion_builder
from .node_predicates import concatenate_node_predicates
from .typing import NodePredicates
from ..graph import BELGraph
from ...dsl import BaseEntity
from ...typing import Strings

__all__ = [
    'filter_nodes',
    'get_nodes',
    'count_passed_node_filter',
    'summarize_node_filter',
    'get_nodes_by_function',
    'get_nodes_by_namespace',
]


def filter_nodes(graph: BELGraph, node_predicates: NodePredicates) -> Iterable[BaseEntity]:
    """Apply a set of predicates to the nodes iterator of a BEL graph."""
    concatenated_predicate = concatenate_node_predicates(node_predicates=node_predicates)
    for node in graph:
        if concatenated_predicate(graph, node):
            yield node


def get_nodes(graph: BELGraph, node_predicates: NodePredicates) -> Set[BaseEntity]:
    """Get the set of all nodes that pass the predicates."""
    return set(filter_nodes(graph, node_predicates=node_predicates))


def count_passed_node_filter(graph: BELGraph, node_predicates: NodePredicates) -> int:
    """Count how many nodes pass a given set of node predicates."""
    return sum(1 for _ in filter_nodes(graph, node_predicates=node_predicates))


def summarize_node_filter(graph: BELGraph, node_filters: NodePredicates) -> None:
    """Print a summary of the number of nodes passing a given set of filters.

    :param graph: A BEL graph
    :param node_filters: A node filter or list/tuple of node filters
    """
    passed = count_passed_node_filter(graph, node_filters)
    print('{}/{} nodes passed'.format(passed, graph.number_of_nodes()))


def get_nodes_by_function(graph: BELGraph, func: Strings) -> Set[BaseEntity]:
    """Get all nodes with the given function(s)."""
    return get_nodes(graph, function_inclusion_filter_builder(func))


def get_nodes_by_namespace(graph, namespaces: Strings) -> Set[BaseEntity]:
    """Get all nodes identified by the given namespace(s)."""
    return get_nodes(graph, namespace_inclusion_builder(namespaces))
