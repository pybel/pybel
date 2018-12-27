# -*- coding: utf-8 -*-

"""Predicates for edge data from BEL graphs."""

from functools import wraps
from typing import Any, Callable, Optional

from .typing import EdgePredicate
from .utils import part_has_modifier
from ..graph import BELGraph
from ...constants import (
    ACTIVITY, ANNOTATIONS, ASSOCIATION, CAUSAL_RELATIONS, CITATION, CITATION_AUTHORS, CITATION_TYPE,
    CITATION_TYPE_PUBMED, DEGRADATION, DIRECT_CAUSAL_RELATIONS, EVIDENCE, OBJECT, POLAR_RELATIONS, RELATION, SUBJECT,
    TRANSLOCATION,
)
from ...dsl import BaseEntity, BiologicalProcess, Pathology
from ...typing import EdgeData

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
    'has_pathology_causal',
]

DictEdgePredicate = Callable[[EdgeData], bool]


def edge_predicate(func: DictEdgePredicate) -> EdgePredicate:  # noqa: D202
    """Decorate an edge predicate function that only takes a dictionary as its singular argument.

    Apply this as a decorator to a function that takes a single argument, a PyBEL node data dictionary, to make
    sure that it can also accept a pair of arguments, a BELGraph and a PyBEL node tuple as well.
    """

    @wraps(func)
    def _wrapped(*args):
        x = args[0]

        if isinstance(x, BELGraph):
            u, v, k = args[1:4]
            return func(x[u][v][k])

        return func(*args)

    return _wrapped


def keep_edge_permissive(*args, **kwargs) -> bool:
    """Return true for all edges.

    :param dict data: A PyBEL edge data dictionary from a :class:`pybel.BELGraph`
    :return: Always returns :code:`True`
    """
    return True


@edge_predicate
def has_provenance(edge_data: EdgeData) -> bool:
    """Check if the edge has provenance information (i.e. citation and evidence)."""
    return CITATION in edge_data and EVIDENCE in edge_data


@edge_predicate
def has_pubmed(edge_data: EdgeData) -> bool:
    """Check if the edge has a PubMed citation."""
    return CITATION in edge_data and CITATION_TYPE_PUBMED == edge_data[CITATION][CITATION_TYPE]


@edge_predicate
def has_authors(edge_data: EdgeData) -> bool:
    """Check if the edge contains author information for its citation."""
    return CITATION in edge_data and CITATION_AUTHORS in edge_data[CITATION] and edge_data[CITATION][CITATION_AUTHORS]


@edge_predicate
def is_causal_relation(edge_data: EdgeData) -> bool:
    """Check if the given relation is causal."""
    return edge_data[RELATION] in CAUSAL_RELATIONS


@edge_predicate
def is_direct_causal_relation(edge_data: EdgeData) -> bool:
    """Check if the edge is a direct causal relation."""
    return edge_data[RELATION] in DIRECT_CAUSAL_RELATIONS


@edge_predicate
def is_associative_relation(edge_data: EdgeData) -> bool:
    """Check if the edge has an association relation."""
    return edge_data[RELATION] == ASSOCIATION


@edge_predicate
def has_polarity(edge_data: EdgeData) -> bool:
    """Check if the edge has polarity."""
    return edge_data[RELATION] in POLAR_RELATIONS


def _has_modifier(edge_data: EdgeData, modifier: str) -> bool:
    """Check if the edge has the given modifier.

    :param edge_data: The edge data dictionary
    :param modifier: The modifier to check. One of :data:`pybel.constants.ACTIVITY`,
                        :data:`pybel.constants.DEGRADATION`, or :data:`pybel.constants.TRANSLOCATION`.
    :return: Does either the subject or object have the given modifier
    """
    return part_has_modifier(edge_data, SUBJECT, modifier) or part_has_modifier(edge_data, OBJECT, modifier)


@edge_predicate
def edge_has_activity(edge_data: EdgeData) -> bool:
    """Check if the edge contains an activity in either the subject or object."""
    return _has_modifier(edge_data, ACTIVITY)


@edge_predicate
def edge_has_translocation(edge_data: EdgeData) -> bool:
    """Check if the edge has a translocation in either the subject or object."""
    return _has_modifier(edge_data, TRANSLOCATION)


@edge_predicate
def edge_has_degradation(edge_data: EdgeData) -> bool:
    """Check if the edge contains a degradation in either the subject or object."""
    return _has_modifier(edge_data, DEGRADATION)


def edge_has_annotation(edge_data: EdgeData, key: str) -> Optional[Any]:
    """Check if an edge has the given annotation.

    :param edge_data: The data dictionary from a BELGraph's edge
    :param key: An annotation key
    :return: If the annotation key is present in the current data dictionary

    For example, it might be useful to print all edges that are annotated with 'Subgraph':

    >>> from pybel.examples import sialic_acid_graph
    >>> for u, v, data in sialic_acid_graph.edges(data=True):
    >>>     if edge_has_annotation(data, 'Species')
    >>>         print(u, v, data)
    """
    annotations = edge_data.get(ANNOTATIONS)

    if annotations is None:
        return None

    return annotations.get(key)


def has_pathology_causal(graph: BELGraph, u: BaseEntity, v: BaseEntity, k: str) -> bool:
    """Check if the subject is a pathology and has a causal relationship with a non bioprocess/pathology.

    :return: If the subject of this edge is a pathology and it participates in a causal reaction.
    """
    return (
        isinstance(u, Pathology) and
        is_causal_relation(graph, u, v, k) and
        not isinstance(v, (Pathology, BiologicalProcess))
    )
