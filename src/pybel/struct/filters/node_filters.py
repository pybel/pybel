# -*- coding: utf-8 -*-

"""Filter functions for nodes in BEL graphs.

A node predicate is a function that takes two arguments: a :class:`BELGraph` and a node. It returns a boolean
representing whether the node passed the given test.

This module contains a set of default functions for filtering lists of nodes and building node predicates.

A general use for a node predicate is to use the built-in :func:`filter` in code like
:code:`filter(your_node_predicate, graph)`
"""

from typing import Iterable, Set

from .typing import NodePredicate, NodePredicates
from ..graph import BELGraph
from ...dsl import BaseEntity

__all__ = [
    'invert_node_predicate',
    'concatenate_node_predicates',
    'filter_nodes',
    'get_nodes',
    'count_passed_node_filter',
]


def invert_node_predicate(node_predicate: NodePredicate) -> NodePredicate:  # noqa: D202
    """Build a node predicate that is the inverse of the given node predicate."""

    def inverse_predicate(graph: BELGraph, node: BaseEntity) -> bool:
        """Return the inverse of the enclosed node predicate applied to the graph and node."""
        return not node_predicate(graph, node)

    return inverse_predicate


def concatenate_node_predicates(node_predicates: NodePredicates) -> NodePredicate:
    """Concatenate multiple node predicates to a new predicate that requires all predicates to be met.

    Example usage:

    >>> from pybel.dsl import protein, gene
    >>> from pybel.struct.filters.node_predicates import not_pathology, node_exclusion_predicate_builder
    >>> app_protein = protein(name='APP', namespace='HGNC')
    >>> app_gene = gene(name='APP', namespace='HGNC')
    >>> app_predicate = node_exclusion_predicate_builder([app_protein, app_gene])
    >>> my_predicate = concatenate_node_predicates([not_pathology, app_predicate])
    """
    # If a predicate outside a list is given, just return it
    if not isinstance(node_predicates, Iterable):
        return node_predicates

    node_predicates = tuple(node_predicates)

    # If only one predicate is given, don't bother wrapping it
    if 1 == len(node_predicates):
        return node_predicates[0]

    def concatenated_node_predicate(graph: BELGraph, node: BaseEntity) -> bool:
        """Pass only for a nodes that pass all enclosed predicates."""
        return all(
            node_predicate(graph, node)
            for node_predicate in node_predicates
        )

    return concatenated_node_predicate


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
