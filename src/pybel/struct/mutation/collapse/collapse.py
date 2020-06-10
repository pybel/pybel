# -*- coding: utf-8 -*-

"""Utilities for functions for collapsing nodes."""

import itertools as itt
from typing import Mapping, Set

from ...filters.edge_filters import filter_edges
from ...filters.edge_predicate_builders import build_relation_predicate
from ...pipeline import in_place_transformation
from ....constants import HAS_VARIANT
from ....dsl import BaseEntity
from ....utils import hash_edge

__all__ = [
    'collapse_pair',
    'collapse_nodes',
    'collapse_all_variants',
    'surviors_are_inconsistent',
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
def collapse_pair(graph, survivor: BaseEntity, victim: BaseEntity) -> None:
    """Rewire all edges from the synonymous node to the survivor node, then deletes the synonymous node.

    Does not keep edges between the two nodes.

    :param pybel.BELGraph graph: A BEL graph
    :param survivor: The BEL node to collapse all edges on the synonym to
    :param victim: The BEL node to collapse into the surviving node
    """
    graph.add_edges_from(
        (survivor, successor, hash_edge(survivor, successor, edge_data), edge_data)
        for _, successor, edge_data in graph.out_edges(victim, data=True)
        if successor != survivor
    )

    graph.add_edges_from(
        (predecessor, survivor, hash_edge(predecessor, survivor, edge_data), edge_data)
        for predecessor, _, edge_data in graph.in_edges(victim, data=True)
        if predecessor != survivor
    )

    if victim in graph:
        graph.remove_node(victim)


# TODO what happens when collapsing is not consistent? Need to build intermediate mappings and test their consistency.

@in_place_transformation
def collapse_nodes(graph, survivor_mapping: Mapping[BaseEntity, Set[BaseEntity]]) -> None:
    """Collapse all nodes in values to the key nodes, in place.

    :param pybel.BELGraph graph: A BEL graph
    :param survivor_mapping: A dictionary with survivors as their keys, and iterables of the corresponding victims as
     values.
    """
    inconsistencies = surviors_are_inconsistent(survivor_mapping)
    if inconsistencies:
        raise ValueError('survivor mapping is inconsistent: {}'.format(inconsistencies))

    for survivor, victims in survivor_mapping.items():
        for victim in victims:
            collapse_pair(graph, survivor=survivor, victim=victim)

    _remove_self_edges(graph)


def surviors_are_inconsistent(survivor_mapping: Mapping[BaseEntity, Set[BaseEntity]]) -> Set[BaseEntity]:
    """Check that there's no transitive shit going on."""
    victim_mapping = set()
    for victim in itt.chain.from_iterable(survivor_mapping.values()):
        if victim in survivor_mapping:
            victim_mapping.add(victim)
    return victim_mapping


@in_place_transformation
def collapse_all_variants(graph) -> None:
    """Collapse all genes', RNAs', miRNAs', and proteins' variants to their parents.

    :param pybel.BELGraph graph: A BEL Graph
    """
    has_variant_predicate = build_relation_predicate(HAS_VARIANT)

    edges = list(filter_edges(graph, has_variant_predicate))

    for u, v, _ in edges:
        collapse_pair(graph, survivor=u, victim=v)

    _remove_self_edges(graph)
