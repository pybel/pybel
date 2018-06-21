# -*- coding: utf-8 -*-

from collections import defaultdict

import logging

from .utils import update_metadata
from ...constants import ANNOTATIONS

log = logging.getLogger(__name__)

__all__ = [
    'get_subgraphs_by_annotation',
]


def _get_subgraphs_by_annotation_disregard_undefined(graph, annotation):
    result = defaultdict(graph.fresh_copy)

    for source, target, key, data in graph.edges_iter(keys=True, data=True):
        annotation_dict = data.get(ANNOTATIONS)

        if annotation_dict is None:
            continue

        if annotation not in annotation_dict:
            continue

        for value in annotation_dict[annotation]:
            result[value].add_edge(source, target, key=key, **data)

    return dict(result)


def _get_subgraphs_by_annotation_keep_undefined(graph, annotation, sentinel):
    result = defaultdict(graph.fresh_copy)

    for source, target, key, data in graph.edges_iter(keys=True, data=True):
        annotation_dict = data.get(ANNOTATIONS)

        if annotation_dict is None or annotation not in annotation_dict:
            result[sentinel].add_edge(source, target, key=key, **data)
        else:
            for value in annotation_dict[annotation]:
                result[value].add_edge(source, target, key=key, **data)

    return dict(result)


def get_subgraphs_by_annotation(graph, annotation, sentinel=None):
    """Stratifies the given graph into sub-graphs based on the values for edges' annotations

    :param pybel.BELGraph graph: A BEL graph
    :param str annotation: The annotation to group by
    :param Optional[str] sentinel: The value to stick unannotated edges into. If none, does not keep undefined.
    :rtype: dict[str,pybel.BELGraph]
    """
    if sentinel is not None:
        rv = _get_subgraphs_by_annotation_keep_undefined(graph, annotation, sentinel)
    else:
        rv = _get_subgraphs_by_annotation_disregard_undefined(graph, annotation)

    for value in rv.values():
        update_metadata(value, graph)

    return rv
