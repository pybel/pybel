# -*- coding: utf-8 -*-

"""Functions for predicates for edge data from BEL graphs."""

from typing import Iterable, Mapping

from .edge_predicates import edge_predicate, has_authors, has_pubmed, keep_edge_permissive
from .typing import EdgePredicate
from ..graph import BELGraph
from ...constants import ANNOTATIONS, CAUSAL_RELATIONS, CITATION, CITATION_AUTHORS, CITATION_REFERENCE, RELATION
from ...dsl import BaseEntity
from ...typing import EdgeData, Strings

__all__ = [
    'build_annotation_dict_all_filter',
    'build_annotation_dict_any_filter',
    'build_upstream_edge_predicate',
    'build_downstream_edge_predicate',
    'build_relation_predicate',
    'build_pmid_inclusion_filter',
    'build_author_inclusion_filter',
]


def _annotation_dict_all_filter(edge_data: EdgeData, query: Mapping[str, Iterable[str]]) -> bool:
    """Match edges with the given dictionary as a sub-dictionary.

    :param query: The annotation query dict to match
    """
    annotations = edge_data.get(ANNOTATIONS)

    if annotations is None:
        return False

    for key, values in query.items():
        ak = annotations.get(key)

        if ak is None:
            return False

        for value in values:
            if value not in ak:
                return False

    return True


def build_annotation_dict_all_filter(annotations: Mapping[str, Iterable[str]]) -> EdgePredicate:
    """Build an edge predicate for edges whose annotations are super-dictionaries of the given dictionary.

    If no annotations are given, will always evaluate to true.

    :param annotations: The annotation query dict to match
    """
    if not annotations:
        return keep_edge_permissive

    @edge_predicate
    def annotation_dict_all_filter(edge_data: EdgeData) -> bool:
        """Check if the all of the annotations in the enclosed query match."""
        return _annotation_dict_all_filter(edge_data, query=annotations)

    return annotation_dict_all_filter


def _annotation_dict_any_filter(edge_data: EdgeData, query: Mapping[str, Iterable[str]]) -> bool:
    """Match edges with the given dictionary as a sub-dictionary.

    :param query: The annotation query dict to match
    """
    annotations = edge_data.get(ANNOTATIONS)

    if annotations is None:
        return False

    return any(
        key in annotations and value in annotations[key]
        for key, values in query.items()
        for value in values
    )


def build_annotation_dict_any_filter(annotations: Mapping[str, Iterable[str]]) -> EdgePredicate:
    """Build an edge predicate that passes for edges whose data dictionaries match the given dictionary.

    If the given dictionary is empty, will always evaluate to true.

    :param annotations: The annotation query dict to match
    """
    if not annotations:
        return keep_edge_permissive

    @edge_predicate
    def annotation_dict_any_filter(edge_data: EdgeData) -> bool:
        """Check if the any of the annotations in the enclosed query match."""
        return _annotation_dict_any_filter(edge_data, query=annotations)

    return annotation_dict_any_filter


def build_upstream_edge_predicate(nodes: Iterable[BaseEntity]) -> EdgePredicate:
    """Build an edge predicate that pass for relations for which one of the given nodes is the object."""
    nodes = set(nodes)

    def upstream_filter(graph: BELGraph, u: BaseEntity, v: BaseEntity, k: str) -> bool:
        """Pass for relations for which one of the given nodes is the object."""
        return v in nodes and graph[u][v][k][RELATION] in CAUSAL_RELATIONS

    return upstream_filter


def build_downstream_edge_predicate(nodes: Iterable[BaseEntity]) -> EdgePredicate:
    """Build an edge predicate that passes for edges for which one of the given nodes is the subject."""
    nodes = set(nodes)

    def downstream_filter(graph: BELGraph, u: BaseEntity, v: BaseEntity, k: str) -> bool:
        """Pass for relations for which one of the given nodes is the subject."""
        return u in nodes and graph[u][v][k][RELATION] in CAUSAL_RELATIONS

    return downstream_filter


def build_relation_predicate(relations: Strings) -> EdgePredicate:
    """Build an edge predicate that passes for edges with the given relation."""
    if isinstance(relations, str):
        @edge_predicate
        def relation_predicate(edge_data: EdgeData) -> bool:
            """Pass for relations matching the enclosed value."""
            return edge_data[RELATION] == relations

    elif isinstance(relations, Iterable):
        relation_set = set(relations)

        @edge_predicate
        def relation_predicate(edge_data: EdgeData) -> bool:
            """Pass for relations matching the enclosed values."""
            return edge_data[RELATION] in relation_set

    else:
        raise TypeError

    return relation_predicate


def build_pmid_inclusion_filter(pmids: Strings) -> EdgePredicate:
    """Build an edge predicate that passes for edges with citations from the given PubMed identifier(s).

    :param pmids: A PubMed identifier or list of PubMed identifiers to filter for
    """
    if isinstance(pmids, str):
        @edge_predicate
        def pmid_inclusion_filter(edge_data: EdgeData) -> bool:
            """Pass for edges with PubMed citations matching the contained PubMed identifier."""
            return has_pubmed(edge_data) and edge_data[CITATION][CITATION_REFERENCE] == pmids

    elif isinstance(pmids, Iterable):
        pmids = set(pmids)

        @edge_predicate
        def pmid_inclusion_filter(edge_data: EdgeData) -> bool:
            """Pass for edges with PubMed citations matching one of the contained PubMed identifiers."""
            return has_pubmed(edge_data) and edge_data[CITATION][CITATION_REFERENCE] in pmids

    else:
        raise TypeError

    return pmid_inclusion_filter


def build_author_inclusion_filter(authors: Strings) -> EdgePredicate:
    """Build an edge predicate that passes for edges with citations written by the given author(s)."""
    if isinstance(authors, str):
        @edge_predicate
        def author_filter(edge_data: EdgeData) -> bool:
            """Pass for edges with citations with an author that matches the contained author."""
            return has_authors(edge_data) and authors in edge_data[CITATION][CITATION_AUTHORS]

    elif isinstance(authors, Iterable):
        authors = set(authors)

        @edge_predicate
        def author_filter(edge_data: EdgeData) -> bool:
            """Pass for edges with citations with an author that matches one or more of the contained authors."""
            return has_authors(edge_data) and any(
                author in edge_data[CITATION][CITATION_AUTHORS]
                for author in authors
            )

    else:
        raise TypeError

    return author_filter
