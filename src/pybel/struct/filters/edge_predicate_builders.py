# -*- coding: utf-8 -*-


from .edge_predicates import edge_predicate, keep_edge_permissive
from ...constants import ANNOTATIONS, CAUSAL_RELATIONS, RELATION

__all__ = [
    'build_annotation_dict_all_filter',
    'build_annotation_dict_any_filter',
    'build_upstream_edge_predicate',
    'build_downstream_edge_predicate',
    'build_relation_predicate',
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
