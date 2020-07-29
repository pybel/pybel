# -*- coding: utf-8 -*-

"""Functions for inducing graphs based on edge annotations."""

import logging
from typing import Iterable, Optional, Union

from .utils import get_subgraph_by_edge_filter
from ...filters.edge_predicate_builders import build_annotation_dict_all_filter, build_annotation_dict_any_filter
from ...graph import AnnotationsHint, BELGraph
from ...pipeline import transformation

__all__ = [
    'get_subgraph_by_annotation_value',
    'get_subgraph_by_annotations',
]

logger = logging.getLogger(__name__)


@transformation
def get_subgraph_by_annotations(
    graph: BELGraph,
    annotations: AnnotationsHint,
    or_: Optional[bool] = None,
) -> BELGraph:
    """Induce a sub-graph given an annotations filter.

    :param graph: A BEL graph
    :param annotations: Annotation filters (match all with :func:`pybel.utils.subdict_matches`)
    :param or_: if True any annotation should be present, if False all annotations should be present in the
     edge. Defaults to True.
    :return: A subgraph of the original BEL graph
    """
    edge_filter_builder = (
        build_annotation_dict_any_filter
        if (or_ is None or or_) else
        build_annotation_dict_all_filter
    )

    annotations = graph._clean_annotations(annotations)
    return get_subgraph_by_edge_filter(graph, edge_filter_builder(annotations))


@transformation
def get_subgraph_by_annotation_value(graph: BELGraph, annotation: str, values: Union[str, Iterable[str]]) -> BELGraph:
    """Induce a sub-graph over all edges whose annotations match the given key and value.

    :param graph: A BEL graph
    :param annotation: The annotation to group by
    :param values: The value(s) for the annotation
    :return: A subgraph of the original BEL graph
    """
    if isinstance(values, str):
        values = {values}

    return get_subgraph_by_annotations(graph, {annotation: values})
