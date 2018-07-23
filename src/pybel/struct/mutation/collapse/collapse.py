# -*- coding: utf-8 -*-

"""Utilities for functions for collapsing nodes."""

from ...filters import filter_edges
from ...filters.edge_predicate_builders import build_relation_predicate
from ...pipeline import in_place_transformation
from ....constants import HAS_VARIANT, RELATION, unqualified_edges

__all__ = [
    'collapse_pair',
    'collapse_nodes',
    'collapse_all_variants',
]


def _remove_self_edges(graph):
    self_edges = [
        (u, u, k)
        for u in graph
        if u in graph[u]
        for k in graph[u][u]
    ]
    graph.remove_edges_from(self_edges)


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


# TODO what happens when collapsing is not consistent? Need to build intermediate mappings and test their consistency.

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

    _remove_self_edges(graph)


@in_place_transformation
def collapse_all_variants(graph):
    """Collapse all genes', RNAs', miRNAs', and proteins' variants to their parents.

    :param pybel.BELGraph graph: A BEL Graph
    """
    has_variant_predicate = build_relation_predicate(HAS_VARIANT)

    edges = list(filter_edges(graph, has_variant_predicate))

    for u, v, _ in edges:
        collapse_pair(graph, survivor=u, victim=v)

    _remove_self_edges(graph)
