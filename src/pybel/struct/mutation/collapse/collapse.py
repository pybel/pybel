# -*- coding: utf-8 -*-

"""Utilities for functions for collapsing nodes."""

from ...filters import filter_edges
from ...filters.edge_predicate_builders import build_relation_predicate
from ...pipeline import in_place_transformation
from ....constants import HAS_VARIANT, RELATION, unqualified_edges

__all__ = [
    'collapse_pair',
    'collapse_nodes',
    'collapse_edges_passing_predicates',
    'collapse_all_variants',
]


@in_place_transformation
def collapse_pair(graph, survivor, victim):
    """Rewire all edges from the synonymous node to the survivor node, then deletes the synonymous node.

    Does not keep edges between the two nodes.

    :param pybel.BELGraph graph: A BEL graph
    :param tuple survivor: The BEL node to collapse all edges on the synonym to
    :param tuple victim: The BEL node to collapse into the surviving node
    """
    for _, successor, key, data in graph.out_edges(victim, keys=True, data=True):
        if successor == survivor:
            continue

        if data[RELATION] in unqualified_edges:
            graph.add_unqualified_edge(survivor, successor, data[RELATION])
        else:
            graph.add_edge(survivor, successor, key=key, **data)

    for predecessor, _, key, data in graph.in_edges(victim, keys=True, data=True):
        if predecessor == survivor:
            continue

        if data[RELATION] in unqualified_edges:
            graph.add_unqualified_edge(predecessor, survivor, data[RELATION])
        else:
            graph.add_edge(predecessor, survivor, key=key, **data)

    graph.remove_node(victim)


@in_place_transformation
def collapse_nodes(graph, survivor_mapping):
    """Collapse all nodes in values to the key nodes, in place.

    :param pybel.BELGraph graph: A BEL graph
    :param survivor_mapping: A dictionary with survivors as their keys, and iterables of the corresponding victims as
     values.
    :type survivor_mapping: dict[tuple,set[tuple]]
    """
    for survivor, victims in survivor_mapping.items():
        for victim in victims:
            collapse_pair(graph, survivor=survivor, victim=victim)

    # Remove self edges
    graph.remove_edges_from(
        (u, u, k)
        for u in graph
        if u in graph[u]
        for k in graph[u][u]
    )


@in_place_transformation
def collapse_edges_passing_predicates(graph, edge_predicates=None):
    """Collapse all edges passing the given edge predicates.

    :param pybel.BELGraph graph: A BEL Graph
    :param edge_predicates: A predicate or list of predicates
    :type edge_predicates: None or (pybel.BELGraph, tuple, tuple, int) -> bool or iter[(pybel.BELGraph, tuple, tuple, int) -> bool]
    """
    for u, v, _ in filter_edges(graph, edge_predicates=edge_predicates):
        collapse_pair(graph, survivor=u, victim=v)


@in_place_transformation
def collapse_all_variants(graph):
    """Collapse all genes', RNAs', miRNAs', and proteins' variants to their parents.

    :param pybel.BELGraph graph: A BEL Graph
    """
    collapse_edges_passing_predicates(graph, build_relation_predicate(HAS_VARIANT))
