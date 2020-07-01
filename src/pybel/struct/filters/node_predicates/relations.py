# -*- coding: utf-8 -*-

"""Predicate functions for nodes based on their incident edges' relations."""

from typing import Set

from ...graph import BELGraph
from ....constants import CAUSAL_RELATIONS, RELATION
from ....dsl import BaseEntity

__all__ = [
    'has_in_edges',
    'has_causal_out_edges',
    'has_causal_in_edges',
    'has_causal_edges',
    'has_out_edges',
    'is_causal_central',
    'is_causal_sink',
    'is_causal_source',
    'no_causal_out_edges',
    'no_causal_in_edges',
    'no_out_edges',
    'no_in_edges',
    'no_causal_edges',
]


def has_in_edges(graph: BELGraph, node: BaseEntity, edge_types: Set[str]) -> bool:
    """Check if the node has any in-edges in the given set.

    :param graph: A BEL graph
    :param node: A BEL term
    :param edge_types: A collection of edge types to check against
    """
    return any(
        data[RELATION] in edge_types
        for _, _, data in graph.in_edges(node, data=True)
    )


def no_in_edges(graph: BELGraph, node: BaseEntity, edge_types: Set[str]) -> bool:
    """Check if the node does not have any in-edges in the given set.

    :param graph: A BEL graph
    :param node: A BEL term
    :param edge_types: A collection of edge types to check against
    """
    return all(
        data[RELATION] not in edge_types
        for _, _, data in graph.in_edges(node, data=True)
    )


def has_out_edges(graph: BELGraph, node: BaseEntity, edge_types: Set[str]) -> bool:
    """Check if the node has any out-edges in the given set.

    :param graph: A BEL graph
    :param node: A BEL term
    :param edge_types: A collection of edge types to check against
    """
    return any(
        data[RELATION] in edge_types
        for _, _, data in graph.out_edges(node, data=True)
    )


def no_out_edges(graph: BELGraph, node: BaseEntity, edge_types: Set[str]) -> bool:
    """Check if the node does not have any out-edges in the given set.

    :param graph: A BEL graph
    :param node: A BEL term
    :param edge_types: A collection of edge types to check against
    """
    return all(
        data[RELATION] not in edge_types
        for _, _, data in graph.out_edges(node, data=True)
    )


def has_causal_in_edges(graph: BELGraph, node: BaseEntity) -> bool:
    """Check if the node has any causal in-edges.

    :param graph: A BEL graph
    :param node: A BEL term
    """
    return has_in_edges(graph, node, CAUSAL_RELATIONS)


def no_causal_in_edges(graph: BELGraph, node: BaseEntity) -> bool:
    """Check if the node does not have any causal in-edges.

    :param graph: A BEL graph
    :param node: A BEL term
    """
    return no_in_edges(graph, node, CAUSAL_RELATIONS)


def has_causal_out_edges(graph: BELGraph, node: BaseEntity) -> bool:
    """Check if the node has any causal out-edges.

    :param graph: A BEL graph
    :param node: A BEL term
    """
    return has_out_edges(graph, node, CAUSAL_RELATIONS)


def no_causal_out_edges(graph: BELGraph, node: BaseEntity) -> bool:
    """Check if the node does not have any causal out-edges.

    :param graph: A BEL graph
    :param node: A BEL term
    """
    return no_out_edges(graph, node, CAUSAL_RELATIONS)


def has_causal_edges(graph: BELGraph, node: BaseEntity) -> bool:
    """Check if the node has any causal out-edges or in-edges.

    :param graph: A BEL graph
    :param node: A BEL term
    """
    return has_causal_in_edges(graph, node) or has_causal_out_edges(graph, node)


def no_causal_edges(graph: BELGraph, node: BaseEntity) -> bool:
    """Check if the node does not have any causal out-edges or in-edges.

    :param graph: A BEL graph
    :param node: A BEL term
    """
    return no_causal_in_edges(graph, node) and no_causal_out_edges(graph, node)


def is_causal_source(graph: BELGraph, node: BaseEntity) -> bool:
    """Check if the node has causal out-edges but no causal in-edges.

    :param graph: A BEL graph
    :param node: A BEL term
    """
    return no_causal_in_edges(graph, node) and has_causal_out_edges(graph, node)


def is_causal_sink(graph: BELGraph, node: BaseEntity) -> bool:
    """Check if the node has causal in-edges but no causal out-edges.

    :param graph: A BEL graph
    :param node: A BEL term
    """
    return has_causal_in_edges(graph, node) and no_causal_out_edges(graph, node)


def is_causal_central(graph: BELGraph, node: BaseEntity) -> bool:
    """Check if the node has both causal in-edges and also causal out-edges.

    :param graph: A BEL graph
    :param node: A BEL term
    """
    return has_causal_in_edges(graph, node) and has_causal_out_edges(graph, node)
