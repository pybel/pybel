# -*- coding: utf-8 -*-

"""Pre-defined predicates for nodes."""

from ..utils import part_has_modifier
from ...graph import BELGraph
from ....constants import ACTIVITY, DEGRADATION, SOURCE_MODIFIER, TARGET_MODIFIER, TRANSLOCATION
from ....dsl import BaseEntity

__all__ = [
    'has_edge_modifier',
    'has_activity',
    'is_degraded',
    'is_translocated',
]


def has_edge_modifier(graph: BELGraph, node: BaseEntity, modifier: str) -> bool:
    """Return true if over any of a nodes edges, it has a given modifier.

     Modifier can be one of:

     - :data:`pybel.constants.ACTIVITY`,
     - :data:`pybel.constants.DEGRADATION`
     - :data:`pybel.constants.TRANSLOCATION`.

    :param modifier: One of :data:`pybel.constants.ACTIVITY`, :data:`pybel.constants.DEGRADATION`, or
                        :data:`pybel.constants.TRANSLOCATION`
    """
    modifier_in_subject = any(
        part_has_modifier(d, SOURCE_MODIFIER, modifier)
        for _, _, d in graph.out_edges(node, data=True)
    )

    modifier_in_object = any(
        part_has_modifier(d, TARGET_MODIFIER, modifier)
        for _, _, d in graph.in_edges(node, data=True)
    )

    return modifier_in_subject or modifier_in_object


def has_activity(graph: BELGraph, node: BaseEntity) -> bool:
    """Return true if over any of the node's edges, it has a molecular activity."""
    return has_edge_modifier(graph, node, ACTIVITY)


def is_degraded(graph: BELGraph, node: BaseEntity) -> bool:
    """Return true if over any of the node's edges, it is degraded."""
    return has_edge_modifier(graph, node, DEGRADATION)


def is_translocated(graph: BELGraph, node: BaseEntity) -> bool:
    """Return true if over any of the node's edges, it is translocated."""
    return has_edge_modifier(graph, node, TRANSLOCATION)
