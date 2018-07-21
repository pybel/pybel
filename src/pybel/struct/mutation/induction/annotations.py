# -*- coding: utf-8 -*-

import logging

from .utils import get_subgraph_by_edge_filter
from ...filters import build_annotation_dict_all_filter, build_annotation_dict_any_filter
from ...pipeline import transformation

log = logging.getLogger(__name__)

__all__ = [
    'get_subgraph_by_annotation_value',
    'get_subgraph_by_annotations',
]


@transformation
def get_subgraph_by_annotations(graph, annotations, or_=None):
    """Induce a sub-graph given an annotations filter.

    :param graph: pybel.BELGraph graph: A BEL graph
    :param dict[str,set[str]] annotations: Annotation filters (match all with :func:`pybel.utils.subdict_matches`)
    :param boolean or_: if True any annotation should be present, if False all annotations should be present in the
                        edge. Defaults to True.
    :return: A subgraph of the original BEL graph
    :rtype: pybel.BELGraph
    """
    edge_filter_builder = (
        build_annotation_dict_any_filter
        if (or_ is None or or_) else
        build_annotation_dict_all_filter
    )

    return get_subgraph_by_edge_filter(graph, edge_filter_builder(annotations))


@transformation
def get_subgraph_by_annotation_value(graph, annotation, value):
    """Induce a sub-graph over all edges whose annotations match the given key and value.

    :param pybel.BELGraph graph: A BEL graph
    :param str annotation: The annotation to group by
    :param str value: The value for the annotation
    :return: A subgraph of the original BEL graph
    :rtype: pybel.BELGraph
    """
    return get_subgraph_by_annotations(graph, {annotation: {value}})
