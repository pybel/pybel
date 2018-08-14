# -*- coding: utf-8 -*-

"""Functions for grouping sub-graphs."""

import logging
from collections import defaultdict

from .utils import cleanup
from ...constants import ANNOTATIONS

log = logging.getLogger(__name__)

__all__ = [
    'get_subgraphs_by_annotation',
]


def _get_subgraphs_by_annotation_disregard_undefined(graph, annotation):
    result = defaultdict(graph.fresh_copy)

    for source, target, key, data in graph.edges(keys=True, data=True):
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

    for source, target, key, data in graph.edges(keys=True, data=True):
        annotation_dict = data.get(ANNOTATIONS)

        if annotation_dict is None or annotation not in annotation_dict:
            result[sentinel].add_edge(source, target, key=key, **data)
        else:
            for value in annotation_dict[annotation]:
                result[value].add_edge(source, target, key=key, **data)

    return dict(result)


def get_subgraphs_by_annotation(graph, annotation, sentinel=None):
    """Stratify the given graph into sub-graphs based on the values for edges' annotations.

    :param pybel.BELGraph graph: A BEL graph
    :param str annotation: The annotation to group by
    :param Optional[str] sentinel: The value to stick unannotated edges into. If none, does not keep undefined.
    :rtype: dict[str,pybel.BELGraph]
    """
    if sentinel is not None:
        subgraphs = _get_subgraphs_by_annotation_keep_undefined(graph, annotation, sentinel)
    else:
        subgraphs = _get_subgraphs_by_annotation_disregard_undefined(graph, annotation)

    cleanup(graph, subgraphs)

    return subgraphs
