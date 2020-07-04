# -*- coding: utf-8 -*-

"""Functions to modify the metadata of graphs, their edges, and their nodes."""

import logging

from ..graph import BELGraph
from ..pipeline import in_place_transformation
from ...constants import ANNOTATIONS, CITATION, IDENTIFIER, NAMESPACE

__all__ = [
    'strip_annotations',
    'add_annotation_value',
    'remove_annotation_value',
    'remove_extra_citation_metadata',
]

logger = logging.getLogger(__name__)


@in_place_transformation
def strip_annotations(graph: BELGraph) -> None:
    """Strip all the annotations from a BEL graph.

    :param graph: A BEL graph
    """
    for u, v, k in graph.edges(keys=True):
        if ANNOTATIONS in graph[u][v][k]:
            del graph[u][v][k][ANNOTATIONS]


@in_place_transformation
def add_annotation_value(graph: BELGraph, annotation: str, value: str, strict: bool = True) -> None:
    """Add the given annotation/value pair to all qualified edges.

    :param graph: A BEL graph
    :param annotation:
    :param value:
    :param strict: Should the function ensure the annotation has already been defined?
    """
    if strict and annotation not in graph.defined_annotation_keywords:
        raise ValueError('annotation not defined: {}'.format(annotation))

    for u, v, k in graph.edges(keys=True):
        if ANNOTATIONS not in graph[u][v][k]:
            continue

        if annotation not in graph[u][v][k][ANNOTATIONS]:
            graph[u][v][k][ANNOTATIONS][annotation] = {}

        graph[u][v][k][ANNOTATIONS][annotation][value] = True


@in_place_transformation
def remove_annotation_value(graph: BELGraph, annotation: str, value: str) -> None:
    """Remove the given annotation/value pair to all qualified edges.

    :param graph: A BEL graph
    :param annotation:
    :param value:
    """
    if annotation not in graph.defined_annotation_keywords:
        logger.warning('annotation was not defined: %s', annotation)
        return

    for u, v, k in graph.edges(keys=True):
        if ANNOTATIONS not in graph[u][v][k]:
            continue

        if annotation not in graph[u][v][k][ANNOTATIONS]:
            continue

        if value not in graph[u][v][k][ANNOTATIONS][annotation]:
            continue

        del graph[u][v][k][ANNOTATIONS][annotation][value]


_CITATION_KEEP_KEYS = {IDENTIFIER, NAMESPACE}


@in_place_transformation
def remove_extra_citation_metadata(graph) -> None:
    """Remove superfluous metadata associated with a citation (that isn't the db/id).

    Best practice is to add this information programmatically.
    """
    for u, v, k in graph.edges(keys=True):
        if CITATION not in graph[u][v][k]:
            continue
        for key in list(graph[u][v][k][CITATION]):
            if key not in _CITATION_KEEP_KEYS:
                del graph[u][v][k][CITATION][key]
