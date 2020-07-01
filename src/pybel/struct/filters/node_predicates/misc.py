# -*- coding: utf-8 -*-

"""Misc node predicates."""

from typing import Iterable, Type

from .utils import node_predicate
from ..typing import NodePredicate
from ...graph import BELGraph
from ....constants import PART_OF, RELATION
from ....dsl import BaseEntity, ListAbundance

__all__ = [
    'none_of',
    'one_of',
    'is_isolated_list_abundance',
]


def none_of(nodes: Iterable[BaseEntity]) -> NodePredicate:
    """Build a node predicate that returns false for the given nodes."""
    nodes = set(nodes)

    @node_predicate
    def _predicate(node: BaseEntity) -> bool:
        """Return true if the node is not in the given set of nodes."""
        return node not in nodes

    return _predicate


def one_of(nodes: Iterable[BaseEntity]) -> NodePredicate:
    """Build a function that returns true for the given nodes."""
    nodes = set(nodes)

    @node_predicate
    def _predicate(node: BaseEntity) -> bool:
        """Return true if the node is in the given set of nodes."""
        return node in nodes

    return _predicate


def is_isolated_list_abundance(
    graph: BELGraph,
    node: BaseEntity,
    cls: Type[ListAbundance] = ListAbundance,
) -> bool:
    """Return if the node is a list abundance but has no qualified edges."""
    return (
        isinstance(node, cls)
        and 0 == graph.out_degree(node)
        and all(
            data[RELATION] == PART_OF
            for _, __, data in graph.in_edges(node, data=True)
        )
    )
