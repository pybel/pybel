# -*- coding: utf-8 -*-

from collections import Iterable

from six import string_types

from .edge_predicates import edge_predicate, has_authors, has_pubmed, keep_edge_permissive
from ...constants import ANNOTATIONS, CAUSAL_RELATIONS, CITATION, CITATION_AUTHORS, CITATION_REFERENCE, RELATION

__all__ = [
    'build_annotation_dict_all_filter',
    'build_annotation_dict_any_filter',
    'build_upstream_edge_predicate',
    'build_downstream_edge_predicate',
    'build_relation_predicate',
    'build_pmid_inclusion_filter',
    'build_author_inclusion_filter',
]


def _annotation_dict_all_filter(data, query):
    """A filter that matches edges with the given dictionary as a sub-dictionary

    :param dict data: A PyBEL edge data dictionary
    :param dict query: The annotation query dict to match
    :rtype: bool
    """
    annotations = data.get(ANNOTATIONS)

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


def build_annotation_dict_all_filter(annotations):
    """Build an edge predicate that passes for edges whose data dictionaries's annotations entry are super-dictionaries
    to the given dictionary.

    If no annotations are given, will always evaluate to true.

    :param dict annotations: The annotation query dict to match
    :rtype: (pybel.BELGraph, tuple, tuple, int) -> bool
    """
    if not annotations:
        return keep_edge_permissive

    @edge_predicate
    def annotation_dict_all_filter(data):
        """Checks if the all of the annotations in the enclosed query match

        :param dict data: A PyBEL edge data dictionary
        :rtype: bool
        """
        return _annotation_dict_all_filter(data, query=annotations)

    return annotation_dict_all_filter


def _annotation_dict_any_filter(data, query):
    """A filter that matches edges with the given dictionary as a sub-dictionary

    :param dict data: A PyBEL edge data dictionary
    :param dict query: The annotation query dict to match
    :rtype: bool
    """
    annotations = data.get(ANNOTATIONS)

    if annotations is None:
        return False

    return any(
        key in annotations and value in annotations[key]
        for key, values in query.items()
        for value in values
    )


def build_annotation_dict_any_filter(annotations):
    """Build an edge predicate that passes for edges whose data dictionaries match the given dictionary.

    If the given dictionary is empty, will always evaluate to true.

    :param dict annotations: The annotation query dict to match
    :rtype: (pybel.BELGraph, tuple, tuple, int) -> bool
    """
    if not annotations:
        return keep_edge_permissive

    @edge_predicate
    def annotation_dict_any_filter(data):
        """Checks if the any of the annotations in the enclosed query match

        :param dict data: A PyBEL edge data dictionary
        :rtype: bool
        """
        return _annotation_dict_any_filter(data, query=annotations)

    return annotation_dict_any_filter


def build_upstream_edge_predicate(nodes):
    """Build an edge predicate that pass for relations for which one of the given nodes is the object.

    :param iter[tuple] nodes: An iterable of PyBEL node tuples
    :rtype: (pybel.BELGraph, tuple, tuple, int) -> bool
    """
    nodes = set(nodes)

    def upstream_filter(graph, u, v, k):
        """Pass for relations for which one of the given nodes is the object.

        :type graph: pybel.BELGraph
        :type u: tuple
        :type v: tuple
        :type k: int
        :rtype: bool
        """
        return v in nodes and graph[u][v][k][RELATION] in CAUSAL_RELATIONS

    return upstream_filter


def build_downstream_edge_predicate(nodes):
    """Build an edge predicate that passes for edges for which one of the given nodes is the subject.

    :param iter[tuple] nodes: An iterable of PyBEL node tuples
    :rtype: (pybel.BELGraph, tuple, tuple, int) -> bool
    """
    nodes = set(nodes)

    def downstream_filter(graph, u, v, k):
        """Pass for relations for which one of the given nodes is the subject.

        :type graph: pybel.BELGraph
        :type u: tuple
        :type v: tuple
        :type k: int
        :rtype: bool
        """
        return u in nodes and graph[u][v][k][RELATION] in CAUSAL_RELATIONS

    return downstream_filter


def build_relation_predicate(relations):
    """Build an edge predicate that passes for edges with the given relation.

    :param relations: A relation string
    :type relations: str or iter[str]
    :rtype: (pybel.BELGraph, tuple, tuple, int) -> bool
    """
    if isinstance(relations, str):
        @edge_predicate
        def relation_predicate(data):
            """Pass for relations matching the enclosed value.

            :param dict data: A PyBEL edge data dictionary
            :return: If the edge has the contained relation
            :rtype: bool
            """
            return data[RELATION] == relations

        return relation_predicate

    elif isinstance(relations, Iterable):
        relation_set = set(relations)

        @edge_predicate
        def relation_predicate(data):
            """Pass for relations matching the enclosed values.

            :param dict data: A PyBEL edge data dictionary
            :return: If the edge has one of the contained relations
            :rtype: bool
            """
            return data[RELATION] in relation_set

    else:
        raise TypeError

    return relation_predicate


def build_pmid_inclusion_filter(pmids):
    """Build an edge predicate that passes for edges with citations from the given PubMed identifier(s).

    :param pmids: A PubMed identifier or list of PubMed identifiers to filter for
    :type pmids: str or iter[str]
    :return: An edge predicate
    :rtype: (pybel.BELGraph, tuple, tuple, int) -> bool
    """
    if isinstance(pmids, string_types):
        @edge_predicate
        def pmid_inclusion_filter(data):
            """Pass for edges with PubMed citations matching the contained PubMed identifier.

            :param dict data: The edge data dictionary
            :return: If the edge has a PubMed citation with the contained PubMed identifier
            :rtype: bool
            """
            return has_pubmed(data) and data[CITATION][CITATION_REFERENCE] == pmids

    else:
        pmids = set(pmids)

        @edge_predicate
        def pmid_inclusion_filter(data):
            """Pass for edges with PubMed citations matching one of the contained PubMed identifiers.

            :param dict data: The edge data dictionary
            :return: If the edge has a PubMed citation with one of the contained PubMed identifiers
            :rtype: bool
            """
            return has_pubmed(data) and data[CITATION][CITATION_REFERENCE] in pmids

    return pmid_inclusion_filter


def build_author_inclusion_filter(authors):
    """Build an edge predicate that passes for edges with citations written by the given author(s).

    :param authors: An author or list of authors
    :type authors: str or iter[str]
    :return: An edge predicate
    :rtype: (pybel.BELGraph, tuple, tuple, int) -> bool
    """
    if isinstance(authors, string_types):
        @edge_predicate
        def author_filter(data):
            """Pass for edges with citations with an author that matches the contained author.

            :param dict data: The edge data dictionary
            :return: If the edge has a citation with an author that matches the the contained author
            :rtype: bool
            """
            return has_authors(data) and authors in data[CITATION][CITATION_AUTHORS]

    else:
        authors = set(authors)

        @edge_predicate
        def author_filter(data):
            """Pass for edges with citations with an author that matches one or more of the contained authors.

            :param dict data: The edge data dictionary
            :return: If the edge has a citation with an author that matches the the contained author
            :rtype: bool
            """
            return has_authors(data) and any(
                author in data[CITATION][CITATION_AUTHORS]
                for author in authors
            )

    return author_filter
