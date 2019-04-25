# -*- coding: utf-8 -*-

"""Pre-defined predicates for nodes."""

from functools import wraps
from typing import Callable, Iterable, Type

from .node_predicate_builders import function_inclusion_filter_builder
from .typing import NodePredicate
from .utils import part_has_modifier
from ..graph import BELGraph
from ...constants import (
    ABUNDANCE, ACTIVITY, CAUSAL_RELATIONS, DEGRADATION, FRAGMENT, FUNCTION, GENE, GMOD, HAS_COMPONENT, HGVS, KIND,
    MIRNA, OBJECT, PATHOLOGY, PMOD, PROTEIN, RELATION, RNA, SUBJECT, TRANSLOCATION, VARIANTS,
)
from ...dsl import BaseEntity, ListAbundance

__all__ = [
    'node_predicate',
    'keep_node_permissive',
    'is_abundance',
    'is_gene',
    'is_protein',
    'is_pathology',
    'not_pathology',
    'has_variant',
    'has_protein_modification',
    'has_gene_modification',
    'has_hgvs',
    'has_fragment',
    'has_activity',
    'is_degraded',
    'is_translocated',
    'has_causal_in_edges',
    'has_causal_out_edges',
    'node_inclusion_predicate_builder',
    'node_exclusion_predicate_builder',
    'is_causal_source',
    'is_causal_sink',
    'is_causal_central',
    'is_isolated_list_abundance',
]


def node_predicate(f: Callable[[BaseEntity], bool]) -> NodePredicate:  # noqa: D202
    """Tag a node predicate that takes a dictionary to also accept a pair of (BELGraph, node).

    Apply this as a decorator to a function that takes a single argument, a PyBEL node, to make
    sure that it can also accept a pair of arguments, a BELGraph and a PyBEL node as well.
    """

    @wraps(f)
    def wrapped(*args):
        x = args[0]

        if isinstance(x, BELGraph):
            return f(args[1], *args[2:])

        # Assume:
        # if isinstance(x, dict):
        return f(*args)

    return wrapped


@node_predicate
def keep_node_permissive(_: BaseEntity) -> bool:
    """Return true for all nodes.

    Given BEL graph :code:`graph`, applying :func:`keep_node_permissive` with a predicate on the nodes iterable
    as in :code:`filter(keep_node_permissive, graph)` will result in the same iterable as iterating directly over a
    :class:`BELGraph`
    """
    return True


@node_predicate
def is_abundance(node: BaseEntity) -> bool:
    """Return true if the node is an abundance."""
    return node[FUNCTION] == ABUNDANCE


@node_predicate
def is_gene(node: BaseEntity) -> bool:
    """Return true if the node is a gene."""
    return node[FUNCTION] == GENE


@node_predicate
def is_protein(node: BaseEntity) -> bool:
    """Return true if the node is a protein."""
    return node[FUNCTION] == PROTEIN


is_central_dogma = function_inclusion_filter_builder([GENE, RNA, MIRNA, PROTEIN])
"""Return true if the node is a gene, RNA, miRNA, or Protein."""


@node_predicate
def is_pathology(node: BaseEntity) -> bool:
    """Return true if the node is a pathology."""
    return node[FUNCTION] == PATHOLOGY


@node_predicate
def not_pathology(node: BaseEntity) -> bool:
    """Return false if the node is a pathology."""
    return node[FUNCTION] != PATHOLOGY


@node_predicate
def has_variant(node: BaseEntity) -> bool:
    """Return true if the node has any variants."""
    return VARIANTS in node


def _node_has_variant(node: BaseEntity, variant: str) -> bool:
    """Return true if the node has at least one of the given variant.

    :param variant: :data:`PMOD`, :data:`HGVS`, :data:`GMOD`, or :data:`FRAGMENT`
    """
    return VARIANTS in node and any(
        variant_dict[KIND] == variant
        for variant_dict in node[VARIANTS]
    )


@node_predicate
def has_protein_modification(node: BaseEntity) -> bool:
    """Return true if the node has a protein modification variant."""
    return _node_has_variant(node, PMOD)


@node_predicate
def has_gene_modification(node: BaseEntity) -> bool:
    """Return true if the node has a gene modification."""
    return _node_has_variant(node, GMOD)


@node_predicate
def has_hgvs(node: BaseEntity) -> bool:
    """Return true if the node has an HGVS variant."""
    return _node_has_variant(node, HGVS)


@node_predicate
def has_fragment(node: BaseEntity) -> bool:
    """Return true if the node has a fragment."""
    return _node_has_variant(node, FRAGMENT)


def _node_has_modifier(graph: BELGraph, node: BaseEntity, modifier: str) -> bool:
    """Return true if over any of a nodes edges, it has a given modifier.

     Modifier can be one of:

     - :data:`pybel.constants.ACTIVITY`,
     - :data:`pybel.constants.DEGRADATION`
     - :data:`pybel.constants.TRANSLOCATION`.

    :param modifier: One of :data:`pybel.constants.ACTIVITY`, :data:`pybel.constants.DEGRADATION`, or
                        :data:`pybel.constants.TRANSLOCATION`
    """
    modifier_in_subject = any(
        part_has_modifier(d, SUBJECT, modifier)
        for _, _, d in graph.out_edges(node, data=True)
    )

    modifier_in_object = any(
        part_has_modifier(d, OBJECT, modifier)
        for _, _, d in graph.in_edges(node, data=True)
    )

    return modifier_in_subject or modifier_in_object


def has_activity(graph: BELGraph, node: BaseEntity) -> bool:
    """Return true if over any of the node's edges, it has a molecular activity."""
    return _node_has_modifier(graph, node, ACTIVITY)


def is_degraded(graph: BELGraph, node: BaseEntity) -> bool:
    """Return true if over any of the node's edges, it is degraded."""
    return _node_has_modifier(graph, node, DEGRADATION)


def is_translocated(graph: BELGraph, node: BaseEntity) -> bool:
    """Return true if over any of the node's edges, it is translocated."""
    return _node_has_modifier(graph, node, TRANSLOCATION)


def has_causal_in_edges(graph: BELGraph, node: BaseEntity) -> bool:
    """Return true if the node contains any in_edges that are causal."""
    return any(
        data[RELATION] in CAUSAL_RELATIONS
        for _, _, data in graph.in_edges(node, data=True)
    )


def has_causal_out_edges(graph: BELGraph, node: BaseEntity) -> bool:
    """Return true if the node contains any out_edges that are causal."""
    return any(
        data[RELATION] in CAUSAL_RELATIONS
        for _, _, data in graph.out_edges(node, data=True)
    )


def node_exclusion_predicate_builder(nodes: Iterable[BaseEntity]) -> NodePredicate:
    """Build a node predicate that returns false for the given nodes."""
    nodes = set(nodes)

    @node_predicate
    def node_exclusion_predicate(node: BaseEntity) -> bool:
        """Return true if the node is not in the given set of nodes."""
        return node not in nodes

    return node_exclusion_predicate


def node_inclusion_predicate_builder(nodes: Iterable[BaseEntity]) -> NodePredicate:
    """Build a function that returns true for the given nodes."""
    nodes = set(nodes)

    @node_predicate
    def node_inclusion_predicate(node: BaseEntity) -> bool:
        """Return true if the node is in the given set of nodes."""
        return node in nodes

    return node_inclusion_predicate


def is_causal_source(graph: BELGraph, node: BaseEntity) -> bool:
    """Return true of the node is a causal source.

    - Doesn't have any causal in edge(s)
    - Does have causal out edge(s)
    """
    # TODO reimplement to be faster
    return not has_causal_in_edges(graph, node) and has_causal_out_edges(graph, node)


def is_causal_sink(graph: BELGraph, node: BaseEntity) -> bool:
    """Return true if the node is a causal sink.

    - Does have causal in edge(s)
    - Doesn't have any causal out edge(s)
    """
    return has_causal_in_edges(graph, node) and not has_causal_out_edges(graph, node)


def is_causal_central(graph: BELGraph, node: BaseEntity) -> bool:
    """Return true if the node is neither a causal sink nor a causal source.

    - Does have causal in edges(s)
    - Does have causal out edge(s)
    """
    return has_causal_in_edges(graph, node) and has_causal_out_edges(graph, node)


def is_isolated_list_abundance(graph: BELGraph, node: BaseEntity, cls: Type[ListAbundance] = ListAbundance) -> bool:
    """Return if the node is a list abundance but has no qualified edges."""
    return (
        isinstance(node, cls) and
        0 == graph.in_degree(node) and
        all(
            data[RELATION] == HAS_COMPONENT
            for _, __, data in graph.out_edges(node, data=True)
        )
    )
