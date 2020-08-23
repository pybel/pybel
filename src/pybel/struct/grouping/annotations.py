# -*- coding: utf-8 -*-

"""Functions for grouping sub-graphs."""

import logging
from collections import defaultdict
from typing import Mapping, Optional

from ..graph import BELGraph
from ...constants import ANNOTATIONS
from ...language import Entity

__all__ = [
    'get_subgraphs_by_annotation',
]

logger = logging.getLogger(__name__)


def _get_subgraphs_by_annotation_disregard_undefined(graph: BELGraph, annotation: str) -> Mapping[Entity, BELGraph]:
    result = defaultdict(graph.child)

    for source, target, key, data in graph.edges(keys=True, data=True):
        annotation_dict = data.get(ANNOTATIONS)

        if annotation_dict is None:
            continue

        if annotation not in annotation_dict:
            continue

        for entity in annotation_dict[annotation]:
            result[entity].add_edge(source, target, key=key, **data)

    return dict(result)


def _get_subgraphs_by_annotation_keep_undefined(
    graph: BELGraph,
    annotation: str,
    sentinel: Optional[str],
) -> Mapping[Entity, BELGraph]:
    result = defaultdict(graph.child)

    for source, target, key, data in graph.edges(keys=True, data=True):
        annotation_dict = data.get(ANNOTATIONS)

        if annotation_dict is None or annotation not in annotation_dict:
            result[sentinel].add_edge(source, target, key=key, **data)
        else:
            for entity in annotation_dict[annotation]:
                result[entity].add_edge(source, target, key=key, **data)

    return dict(result)


def get_subgraphs_by_annotation(
    graph: BELGraph,
    annotation: str,
    sentinel: Optional[str] = None,
) -> Mapping[Entity, BELGraph]:
    """Stratify the given graph into sub-graphs based on the values for edges' annotations.

    :param graph: A BEL graph
    :param annotation: The annotation to group by
    :param sentinel: The value to stick unannotated edges into. If none, does not keep undefined.
    """
    if sentinel is not None:
        subgraphs = _get_subgraphs_by_annotation_keep_undefined(graph, annotation, sentinel)
    else:
        subgraphs = _get_subgraphs_by_annotation_disregard_undefined(graph, annotation)

    return subgraphs
