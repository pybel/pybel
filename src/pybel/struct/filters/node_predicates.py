# -*- coding: utf-8 -*-

from functools import wraps

from .utils import part_has_modifier
from ..graph import BELGraph
from ...constants import (
    ABUNDANCE, ACTIVITY, CAUSAL_RELATIONS, DEGRADATION, FRAGMENT, FUNCTION, GENE, GMOD, HGVS, KIND,
    OBJECT, PATHOLOGY, PMOD, PROTEIN, RELATION, SUBJECT, TRANSLOCATION, VARIANTS,
)
from ...tokens import node_to_tuple

__all__ = [
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
]


def node_predicate(f):
    """Apply this as a decorator to a function that takes a single argument, a PyBEL node data dictionary, to make
    sure that it can also accept a pair of arguments, a BELGraph and a PyBEL node tuple as well.

    :type f: types.FunctionType
    :rtype: types.FunctionType
    """

    @wraps(f)
    def wrapped(*args):
        x = args[0]

        if isinstance(x, BELGraph):
            return f(x.node[args[1]], *args[2:])

        # Assume:
        # if isinstance(x, dict):
        return f(*args)

    return wrapped


def keep_node_permissive(graph, node):
    """A default node predicate that always evaluates to :data:`True`.

    Given BEL graph :code:`graph`, applying :func:`keep_node_permissive` with a predicate on the nodes iterable
    as in :code:`filter(keep_node_permissive, graph)` will result in the same iterable as iterating directly over a
    :class:`BELGraph`

    :param BELGraph graph: A BEL graph
    :param tuple node: The node
    :return: Always returns :data:`True`
    :rtype: bool
    """
    return True


@node_predicate
def is_abundance(data):
    """Returns true if the node is an abundance

    :param dict data: A PyBEL data dictionary
    :rtype: bool
    """
    return data[FUNCTION] == ABUNDANCE


@node_predicate
def is_gene(data):
    """Returns true if the node is a gene

    :param dict data: A PyBEL data dictionary
    :rtype: bool
    """
    return data[FUNCTION] == GENE


@node_predicate
def is_protein(data):
    """Returns true if the node is a protein

    :param dict data: A PyBEL data dictionary
    :rtype: bool
    """
    return data[FUNCTION] == PROTEIN


@node_predicate
def is_pathology(data):
    """Returns true if the node is a pathology

    :param dict data: A PyBEL data dictionary
    :rtype: bool
    """
    return data[FUNCTION] == PATHOLOGY


@node_predicate
def not_pathology(data):
    """Returns false if the node is a pathology

    :param dict data: A PyBEL data dictionary
    :rtype: bool
    """
    return data[FUNCTION] != PATHOLOGY


@node_predicate
def has_variant(data):
    """Returns true if the node has any variants

    :param dict data: A PyBEL data dictionary
    :rtype: bool
    """
    return VARIANTS in data


def _node_has_variant(data, variant):
    """Checks if a node has at least one of the given variant

    :param dict data: A PyBEL data dictionary
    :param str variant: :data:`PMOD`, :data:`HGVS`, :data:`GMOD`, or :data:`FRAGMENT`
    :rtype: bool
    """
    return VARIANTS in data and any(
        variant_dict[KIND] == variant
        for variant_dict in data[VARIANTS]
    )


@node_predicate
def has_protein_modification(data):
    """Returns true if the node has a protein modification variant

    :param dict data: A PyBEL data dictionary
    :rtype: bool
    """
    return _node_has_variant(data, PMOD)


@node_predicate
def has_gene_modification(data):
    """Checks if a node has a gene modification

    :param dict data: A PyBEL data dictionary
    :rtype: bool
    """
    return _node_has_variant(data, GMOD)


@node_predicate
def has_hgvs(data):
    """Checks if a node has an HGVS variant

    :param dict data: A PyBEL data dictionary
    :rtype: bool
    """
    return _node_has_variant(data, HGVS)


@node_predicate
def has_fragment(data):
    """Checks if a node has a fragment

    :param dict data: A PyBEL data dictionary
    :rtype: bool
    """
    return _node_has_variant(data, FRAGMENT)


def _node_has_modifier(graph, node, modifier):
    """Returns true if over any of a nodes edges, it has a given modifier - :data:`pybel.constants.ACTIVITY`,
     :data:`pybel.constants.DEGRADATION`, or :data:`pybel.constants.TRANSLOCATION`.

    :param pybel.BELGraph graph: A BEL graph
    :param tuple node: A BEL node
    :param str modifier: One of :data:`pybel.constants.ACTIVITY`, :data:`pybel.constants.DEGRADATION`, or
                        :data:`pybel.constants.TRANSLOCATION`
    :return: If the node has a known modifier
    :rtype: bool
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


def has_activity(graph, node):
    """Returns true if over any of the node's edges it has a molecular activity

    :param pybel.BELGraph graph: A BEL graph
    :param tuple node: A BEL node
    :return: If the node has a known molecular activity
    :rtype: bool
    """
    return _node_has_modifier(graph, node, ACTIVITY)


def is_degraded(graph, node):
    """Returns true if over any of the node's edges it is degraded

    :param pybel.BELGraph graph: A BEL graph
    :param tuple node: A BEL node
    :return: If the node has a known degradation
    :rtype: bool
    """
    return _node_has_modifier(graph, node, DEGRADATION)


def is_translocated(graph, node):
    """Returns true if over any of the node's edges it is transloated

    :param pybel.BELGraph graph: A BEL graph
    :param tuple node: A BEL node
    :return: If the node has a known translocation
    :rtype: bool
    """
    return _node_has_modifier(graph, node, TRANSLOCATION)


def has_causal_in_edges(graph, node):
    """Returns true if the node contains any in_edges that are causal

    :param pybel.BELGraph graph: A BEL graph
    :param tuple node: A BEL node
    :rtype: bool
    """
    return any(
        data[RELATION] in CAUSAL_RELATIONS
        for _, _, data in graph.in_edges(node, data=True)
    )


def has_causal_out_edges(graph, node):
    """Returns true if the node contains any out_edges that are causal

    :param pybel.BELGraph graph: A BEL graph
    :param tuple node: A BEL node
    :rtype: bool
    """
    return any(
        data[RELATION] in CAUSAL_RELATIONS
        for _, _, data in graph.out_edges(node, data=True)
    )


def _hash_node_list(nodes):
    return {
        node_to_tuple(node) if isinstance(node, dict) else node
        for node in nodes
    }


def node_exclusion_predicate_builder(nodes):
    """Builds a function that returns true

    :param list[tuple or dict] nodes: A list of PyBEL node data dictionaries or PyBEL node tuples
    :rtype: types.FunctionType
    """
    nodes = _hash_node_list(nodes)

    @node_predicate
    def node_exclusion_predicate(data):
        """Returns true if the node is not in the given set of nodes

        :param dict data: A PyBEL data dictionary
        :rtype: bool
        """
        return node_to_tuple(data) not in nodes

    return node_exclusion_predicate


def node_inclusion_predicate_builder(nodes):
    """Builds a function that returns true

    :param list[tuple or dict] nodes: A list of PyBEL node data dictionaries or PyBEL node tuples
    :rtype: types.FunctionType
    """
    nodes = _hash_node_list(nodes)

    @node_predicate
    def node_inclusion_predicate(data):
        """Returns true if the node is in the given set of nodes

        :param dict data: A PyBEL data dictionary
        :rtype: bool
        """
        return node_to_tuple(data) in nodes

    return node_inclusion_predicate


def is_causal_source(graph, node):
    """Is the node is a causal source?

    - Doesn't have any causal in edge(s)
    - Does have causal out edge(s)

    :param pybel.BELGraph graph: A BEL graph
    :param tuple node: A BEL node
    :return: If the node is a causal source
    :rtype: bool
    """
    # TODO reimplement to be faster
    return not has_causal_in_edges(graph, node) and has_causal_out_edges(graph, node)


def is_causal_sink(graph, node):
    """Is the node is a causal sink?

    - Does have causal in edge(s)
    - Doesn't have any causal out edge(s)

    :param pybel.BELGraph graph: A BEL graph
    :param tuple node: A BEL node
    :return: If the node is a causal source
    :rtype: bool
    """
    return has_causal_in_edges(graph, node) and not has_causal_out_edges(graph, node)


def is_causal_central(graph, node):
    """Is the node neither a causal sink nor a causal source?

    - Does have causal in edges(s)
    - Does have causal out edge(s)

    :param pybel.BELGraph graph: A BEL graph
    :param tuple node: A BEL node
    :return: If the node is neither a causal sink nor a causal source
    :rtype: bool
    """
    return has_causal_in_edges(graph, node) and has_causal_out_edges(graph, node)
