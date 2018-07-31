# -*- coding: utf-8 -*-

"""Functions to modify the metadata of graphs, their edges, and their nodes."""

import logging

from ..pipeline import in_place_transformation
from ...constants import ANNOTATIONS

__all__ = [
    'strip_annotations',
    'add_annotation_value',
    'remove_annotation_value',
]

log = logging.getLogger(__name__)


@in_place_transformation
def strip_annotations(graph):
    """Strip all the annotations from a BEL graph.

    :param pybel.BELGraph graph: A BEL graph
    """
    for u, v, k in graph.edges(keys=True):
        if ANNOTATIONS in graph[u][v][k]:
            del graph[u][v][k][ANNOTATIONS]


@in_place_transformation
def add_annotation_value(graph, annotation, value):
    """Add the given annotation/value pair to all qualified edges.

    :param pybel.BELGraph graph:
    :param str annotation:
    :param str value:
    """
    if annotation not in graph.defined_annotation_keywords:
        raise ValueError('annotation not defined: {}'.format(annotation))

    for u, v, k in graph.edges(keys=True):
        if ANNOTATIONS not in graph[u][v][k]:
            continue

        if annotation not in graph[u][v][k][ANNOTATIONS]:
            graph[u][v][k][ANNOTATIONS] = {annotation: {}}

        graph[u][v][k][ANNOTATIONS][annotation][value] = True


@in_place_transformation
def remove_annotation_value(graph, annotation, value):
    """Remove the given annotation/value pair to all qualified edges.

    :param pybel.BELGraph graph:
    :param str annotation:
    :param str value:
    """
    if annotation not in graph.defined_annotation_keywords:
        log.warning('annotation was not defined: %s', annotation)
        return

    for u, v, k in graph.edges(keys=True):
        if ANNOTATIONS not in graph[u][v][k]:
            continue

        if annotation not in graph[u][v][k][ANNOTATIONS]:
            continue

        if value not in graph[u][v][k][ANNOTATIONS][annotation]:
            continue

        del graph[u][v][k][ANNOTATIONS][annotation][value]
