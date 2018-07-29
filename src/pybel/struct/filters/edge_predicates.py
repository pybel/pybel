# -*- coding: utf-8 -*-

from functools import wraps

from .utils import part_has_modifier
from ..graph import BELGraph
from ...constants import (
    ACTIVITY, ANNOTATIONS, ASSOCIATION, CAUSAL_RELATIONS, CITATION, CITATION_AUTHORS,
    CITATION_TYPE, CITATION_TYPE_PUBMED, CORRELATIVE_RELATIONS, DEGRADATION, DIRECT_CAUSAL_RELATIONS, EVIDENCE, OBJECT,
    RELATION, SUBJECT, TRANSLOCATION,
)

__all__ = [
    'edge_predicate',
    'keep_edge_permissive',
    'has_provenance',
    'has_pubmed',
    'has_authors',
    'is_causal_relation',
    'is_direct_causal_relation',
    'is_associative_relation',
    'has_polarity',
    'edge_has_activity',
    'edge_has_degradation',
    'edge_has_translocation',
    'edge_has_annotation',
]


def edge_predicate(f):
    """Apply this as a decorator to a function that takes a single argument, a PyBEL node data dictionary, to make
    sure that it can also accept a pair of arguments, a BELGraph and a PyBEL node tuple as well.

    :type f: (dict) -> bool
    :rtype: (pybel.BELGraph, tuple, tuple, int) -> bool
    """

    @wraps(f)
    def wrapped(*args):
        x = args[0]

        if isinstance(x, BELGraph):
            u, v, k = args[1:4]
            return f(x.edge[u][v][k])

        return f(*args)

    return wrapped


@edge_predicate
def keep_edge_permissive(data):
    """Passes for all edges

    :param dict data: A PyBEL edge data dictionary from a :class:`pybel.BELGraph`
    :return: Always returns :code:`True`
    :rtype: bool
    """
    return True


@edge_predicate
def has_provenance(data):
    """Passes for edges with provenance information (i.e. citation and evidence)

    :param dict data: The edge data dictionary
    :return: If the edge has both a citation and and evidence entry
    :rtype: bool
    """
    return CITATION in data and EVIDENCE in data


@edge_predicate
def has_pubmed(data):
    """Checks if the edge data dictionary has a PubMed citation

    :param dict data: A PyBEL edge data dictionary from a :class:`pybel.BELGraph`
    :return: Does the edge data dictionary has a PubMed citation?
    :rtype: bool
    """
    return CITATION in data and CITATION_TYPE_PUBMED == data[CITATION][CITATION_TYPE]


@edge_predicate
def has_authors(data):
    """Passes for edges that have citations with authors

    :param dict data: A PyBEL edge data dictionary from a :class:`pybel.BELGraph`
    :return: Does the edge's citation data dictionary have authors included?
    :rtype: bool
    """
    return CITATION in data and CITATION_AUTHORS in data[CITATION] and data[CITATION][CITATION_AUTHORS]


@edge_predicate
def is_causal_relation(data):
    """Is the given relation causal?

    :param dict data: The PyBEL edge data dictionary
    :rtype: bool
    """
    return data[RELATION] in CAUSAL_RELATIONS


@edge_predicate
def is_direct_causal_relation(data):
    """Checks if the edge is a direct causal relation

    :param dict data: The PyBEL edge data dictionary
    :rtype: bool
    """
    return data[RELATION] in DIRECT_CAUSAL_RELATIONS


@edge_predicate
def is_associative_relation(data):
    """Only passes on associative edges

    :param dict data: The PyBEL edge data dictionary
    :return: If the edge is a causal edge
    :rtype: bool
    """
    return data[RELATION] == ASSOCIATION


@edge_predicate
def has_polarity(data):
    """Only passes on polarized edges, belonging to the set :data:`pybel.constants.CAUSAL_RELATIONS` or

    :param dict data: The edge data dictionary
    :return: If the edge is a polar edge
    :rtype: bool
    """
    return data[RELATION] in CAUSAL_RELATIONS | CORRELATIVE_RELATIONS


def _has_modifier(data, modifier):
    """Checks if the edge has the given modifier

    :param dict data: The edge data dictionary
    :param str modifier: The modifier to check. One of :data:`pybel.constants.ACTIVITY`,
                        :data:`pybel.constants.DEGRADATION`, or :data:`pybel.constants.TRANSLOCATION`.
    :return: Does either the subject or object have the given modifier
    :rtype: bool
    """
    return (
        part_has_modifier(data, SUBJECT, modifier) or
        part_has_modifier(data, OBJECT, modifier)
    )


@edge_predicate
def edge_has_activity(data):
    """Checks if the edge contains an activity in either the subject or object

    :param dict data: The edge data dictionary
    :return: If the edge contains an activity in either the subject or object
    :rtype: bool
    """
    return _has_modifier(data, ACTIVITY)


@edge_predicate
def edge_has_translocation(data):
    """Checks if the edge has a translocation in either the subject or object

    :param dict data: The edge data dictionary
    :return: If the edge has a translocation in either the subject or object
    :rtype: bool
    """
    return _has_modifier(data, TRANSLOCATION)


@edge_predicate
def edge_has_degradation(data):
    """Checks if the edge contains a degradation in either the subject or object

    :param dict data: The edge data dictionary
    :return: If the edge contains a degradation in either the subject or object
    :rtype: bool
    """
    return _has_modifier(data, DEGRADATION)


def edge_has_annotation(data, key):
    """Checks that ANNOTATION is included in the data dictionary and that the key is also present

    :param dict data: The data dictionary from a BELGraph's edge
    :param str key: An annotation key
    :return: If the annotation key is present in the current data dictionary
    :rtype: Optional[Any]

    For example, it might be useful to print all edges that are annotated with 'Subgraph':

    >>> from pybel.examples import sialic_acid_graph
    >>> for u, v, data in sialic_acid_graph.edges(data=True):
    >>>     if edge_has_annotation(data, 'Species')
    >>>         print(u, v, data)
    """
    annotations = data.get(ANNOTATIONS)

    if annotations is None:
        return

    return annotations.get(key)
