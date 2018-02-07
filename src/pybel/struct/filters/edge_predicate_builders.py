# -*- coding: utf-8 -*-


from .edge_predicates import edge_predicate
from ...constants import ANNOTATIONS

__all__ = [
    'build_annotation_dict_all_filter',
    'build_annotation_dict_any_filter',
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
    dictionary

    :param dict annotations: The annotation query dict to match
    :rtype: types.FunctionType
    """

    @edge_predicate
    def f(data):
        return _annotation_dict_all_filter(data, query=annotations)

    return f


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
    the target dictionary

    :param dict annotations: The annotation query dict to match
    :rtype: types.FunctionType
    """

    @edge_predicate
    def f(data):
        return _annotation_dict_any_filter(data, query=annotations)

    return f
