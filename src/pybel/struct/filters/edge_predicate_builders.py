# -*- coding: utf-8 -*-


from .edge_predicates import edge_has_annotation, edge_predicate
from ...constants import *
from ...utils import subdict_matches

__all__ = [
    'build_annotation_dict_all_filter',
    'build_annotation_dict_any_filter',
]


def build_annotation_dict_all_filter(annotations, partial_match=True):
    """Builds a filter that keeps edges whose data dictionaries's annotations entry are super-dictionaries to the given
    dictionary

    :param dict annotations: The annotation query dict to match
    :param bool partial_match: Should the query values be used as partial or exact matches? Defaults to :code:`True`.
    """

    @edge_predicate
    def annotation_dict_filter(data):
        """A filter that matches edges with the given dictionary as a sub-dictionary"""
        return subdict_matches(data[ANNOTATIONS], annotations, partial_match=partial_match)

    return annotation_dict_filter


def build_annotation_dict_any_filter(annotations):
    """Builds a filter that keeps edges whose data dictionaries's annotations entry contain any match to
    the target dictionary

    :param dict annotations: The annotation query dict to match
    """

    @edge_predicate
    def annotation_dict_filter(data):
        """A filter that matches edges with the given dictionary as a sub-dictionary

        :param dict data: A PyBEL edge data dictionary
        :rtype: bool
        """
        return any(
            edge_has_annotation(data, key) and data[ANNOTATIONS][key] == value
            for key, values in annotations.items()
            for value in values
        )

    return annotation_dict_filter
