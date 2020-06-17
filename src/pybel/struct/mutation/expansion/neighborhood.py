# -*- coding: utf-8 -*-

"""Functions for expanding the neighborhoods of nodes."""

import itertools as itt
from typing import Iterable

from ...filters.node_predicates import is_pathology
from ...filters.typing import EdgeIterator
from ...graph import BELGraph
from ...pipeline import uni_in_place_transformation
from ...utils import update_metadata
from ....dsl import BaseEntity

__all__ = [
    'expand_node_predecessors',
    'expand_node_successors',
    'expand_node_neighborhood',
    'expand_nodes_neighborhoods',
    'expand_all_node_neighborhoods',
    'expand_internal',
]


@uni_in_place_transformation
def expand_node_predecessors(universe: BELGraph, graph: BELGraph, node: BaseEntity):
    """Expand around the predecessors of the given node in the result graph.

    :param universe: The graph containing the stuff to add
    :param graph: The graph to add stuff to
    :param node: A BEL node
    """
    skip_successors = set()
    for successor in universe.successors(node):
        if successor in graph:
            skip_successors.add(successor)
            continue

        graph.add_node_from_data(successor)

    graph.add_edges_from(
        (source, successor, key, data)
        for source, successor, key, data in universe.out_edges(node, data=True, keys=True)
        if successor not in skip_successors
    )
    update_metadata(universe, graph)


@uni_in_place_transformation
def expand_node_successors(universe: BELGraph, graph: BELGraph, node: BaseEntity) -> None:
    """Expand around the successors of the given node in the result graph.

    :param universe: The graph containing the stuff to add
    :param graph: The graph to add stuff to
    :param node: A BEL node
    """
    skip_predecessors = set()
    for predecessor in universe.predecessors(node):
        if predecessor in graph:
            skip_predecessors.add(predecessor)
            continue

        graph.add_node_from_data(predecessor)

    graph.add_edges_from(
        (predecessor, target, key, data)
        for predecessor, target, key, data in universe.in_edges(node, data=True, keys=True)
        if predecessor not in skip_predecessors
    )

    update_metadata(universe, graph)


@uni_in_place_transformation
def expand_node_neighborhood(universe: BELGraph, graph: BELGraph, node: BaseEntity) -> None:
    """Expand around the neighborhoods of the given node in the result graph.

    Note: expands complexes' members

    :param universe: The graph containing the stuff to add
    :param graph: The graph to add stuff to
    :param node: A BEL node
    """
    expand_node_predecessors(universe, graph, node)
    expand_node_successors(universe, graph, node)


@uni_in_place_transformation
def expand_nodes_neighborhoods(universe: BELGraph, graph: BELGraph, nodes: Iterable[BaseEntity]) -> None:
    """Expand around the neighborhoods of the given node in the result graph.

    :param universe: The graph containing the stuff to add
    :param graph: The graph to add stuff to
    :param nodes: Nodes from the query graph
    """
    for node in nodes:
        expand_node_neighborhood(universe, graph, node)


@uni_in_place_transformation
def expand_all_node_neighborhoods(universe: BELGraph, graph: BELGraph, filter_pathologies: bool = False) -> None:
    """Expand the neighborhoods of all nodes in the given graph.

    :param pybel.BELGraph universe: The graph containing the stuff to add
    :param pybel.BELGraph  graph: The graph to add stuff to
    :param filter_pathologies: Should expansion take place around pathologies?
    """
    for node in list(graph):
        if filter_pathologies and is_pathology(node):
            continue

        expand_node_neighborhood(universe, graph, node)


@uni_in_place_transformation
def expand_internal(
    universe: BELGraph,
    graph: BELGraph,
) -> None:
    """Expand on edges between entities in the sub-graph that pass the given filters, in place.

    :param universe: The full graph
    :param graph: A sub-graph to find the upstream information
    """
    for u, v, key in iterate_internal(universe, graph):
        graph.add_edge(u, v, key=key, **universe[u][v][key])


def iterate_internal(universe: BELGraph, graph: BELGraph) -> EdgeIterator:
    """Iterate over edges that are in the universe but not the target graph."""
    for u, v in itt.product(graph, repeat=2):
        if graph.has_edge(u, v) or not universe.has_edge(u, v):
            continue
        for key in universe[u][v]:
            yield u, v, key
