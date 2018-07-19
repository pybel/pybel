# -*- coding: utf-8 -*-

from six import string_types

from .edge_predicates import edge_predicate, has_authors, has_pubmed, keep_edge_permissive
from ...constants import ANNOTATIONS, CAUSAL_RELATIONS, CITATION, CITATION_AUTHORS, CITATION_REFERENCE, RELATION
from ...utils import subdict_matches

__all__ = [
    'build_annotation_dict_all_filter',
    'build_annotation_dict_any_filter',
    'build_upstream_edge_predicate',
    'build_downstream_edge_predicate',
    'build_relation_predicate',
    'build_edge_data_filter',
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
    """Builds a filter that keeps edges whose data dictionaries's annotations entry are super-dictionaries to the given
    dictionary.

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
    """Builds a filter that keeps edges whose data dictionaries's annotations entry contain any match to
    the target dictionary.

    If no annotations are given, will always evaluate to true.

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
    def upstream_filter(graph, u, v, k):
        return v in nodes and graph[u][v][k][RELATION] in CAUSAL_RELATIONS

    return upstream_filter


def build_downstream_edge_predicate(nodes):
    def downstream_filter(graph, u, v, k):
        return u in nodes and graph[u][v][k][RELATION] in CAUSAL_RELATIONS

    return downstream_filter


def build_relation_predicate(relation):
    """Build an edge predicate that matches edges with the given relation

    :param str relation: A relation string
    :rtype: (pybel.BELGraph, tuple, tuple, int) -> bool
    """

    @edge_predicate
    def is_relation(data):
        """Only passes on associative edges

        :param dict data: The PyBEL edge data dictionary
        :return: If the edge is a causal edge
        :rtype: bool
        """
        return data[RELATION] == relation

    return is_relation


def build_edge_data_filter(annotations, partial_match=True):
    """Build a filter that keeps edges whose data dictionaries are super-dictionaries to the given dictionary.

    :param dict annotations: The annotation query dict to match
    :param bool partial_match: Should the query values be used as partial or exact matches? Defaults to :code:`True`.
    :return: An edge predicate
    :rtype: (pybel.BELGraph, tuple, tuple, int) -> bool
    """

    @edge_predicate
    def annotation_dict_filter(data):
        """Pass for edges with the given dictionary as a sub-dictionary.

        :param dict data: The edge data dictionary
        :rtype: bool
        """
        return subdict_matches(data, annotations, partial_match=partial_match)

    return annotation_dict_filter


def build_pmid_inclusion_filter(pmid):
    """Pass for edges with citations whose references are one of the given PubMed identifiers.

    :param pmid: A PubMed identifier or list of PubMed identifiers to filter for
    :type pmid: str or iter[str]
    :return: An edge predicate
    :rtype: (pybel.BELGraph, tuple, tuple, int) -> bool
    """

    if isinstance(pmid, string_types):
        @edge_predicate
        def pmid_inclusion_filter(data):
            """Only passes for edges with PubMed citations matching the contained PubMed identifier

            :param dict data: The edge data dictionary
            :return: If the edge has a PubMed citation with the contained PubMed identifier
            :rtype: bool
            """
            return has_pubmed(data) and data[CITATION][CITATION_REFERENCE] == pmid

        return pmid_inclusion_filter

    else:
        pmids = set(pmid)

        @edge_predicate
        def pmid_inclusion_filter(data):
            """Only passes for edges with PubMed citations matching one of the contained PubMed identifiers

            :param dict data: The edge data dictionary
            :return: If the edge has a PubMed citation with one of the contained PubMed identifiers
            :rtype: bool
            """
            return has_pubmed(data) and data[CITATION][CITATION_REFERENCE] in pmids

        return pmid_inclusion_filter


def build_author_inclusion_filter(author):
    """Build an edge predicate that only passes for edges with author information that matches one of the given authors.

    :param author: An author or list of authors
    :type author: str or iter[str]
    :return: An edge predicate
    :rtype: (pybel.BELGraph, tuple, tuple, int) -> bool
    """
    if isinstance(author, string_types):

        @edge_predicate
        def author_filter(data):
            """Pass for edges with citations with an author that matches the contained author.

            :param dict data: The edge data dictionary
            :return: If the edge has a citation with an author that matches the the contained author
            :rtype: bool
            """
            return has_authors(data) and author in data[CITATION][CITATION_AUTHORS]

        return author_filter

    else:
        authors = set(author)

        @edge_predicate
        def author_filter(data):
            """Pass for edges with citations with an author that matches one or more of the contained authors.

            :param dict data: The edge data dictionary
            :return: If the edge has a citation with an author that matches the the contained author
            :rtype: bool
            """
            return has_authors(data) and any(
                a in data[CITATION][CITATION_AUTHORS]
                for a in authors
            )

        return author_filter
