# -*- coding: utf-8 -*-

"""Functions for getting iterables of nodes."""

from typing import Set

from .node_filters import get_nodes
from .node_predicate_builders import function_inclusion_filter_builder, namespace_inclusion_builder
from ..graph import BELGraph
from ...dsl import BaseEntity
from ...typing import Strings

__all__ = [
    'get_nodes_by_function',
    'get_nodes_by_namespace',
]


def get_nodes_by_function(graph: BELGraph, func: Strings) -> Set[BaseEntity]:
    """Get all nodes with the given function(s)."""
    return get_nodes(graph, function_inclusion_filter_builder(func))


def get_nodes_by_namespace(graph: BELGraph, namespaces: Strings) -> Set[BaseEntity]:
    """Get all nodes identified by the given namespace(s)."""
    return get_nodes(graph, namespace_inclusion_builder(namespaces))
