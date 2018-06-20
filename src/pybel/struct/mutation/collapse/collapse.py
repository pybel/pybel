# -*- coding: utf-8 -*-

"""Utilities for functions for collapsing nodes."""

from ...pipeline import in_place_transformation
from ....constants import RELATION, unqualified_edges

__all__ = [
    'collapse_pair',
    'collapse_nodes',
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
        (u, v, k)
        for u, v, k in graph.edges(keys=True)
        if u == v
    )
