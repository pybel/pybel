# -*- coding: utf-8 -*-

"""Utilities for :mod:`pybel.struct`."""

from ..constants import (
    GRAPH_ANNOTATION_LIST, GRAPH_ANNOTATION_PATTERN, GRAPH_ANNOTATION_URL, GRAPH_NAMESPACE_PATTERN,
    GRAPH_NAMESPACE_URL,
)

__all__ = [
    'update_metadata',
]


def update_metadata(source, target) -> None:
    """Update the namespace and annotation metadata in the target graph.

    :param pybel.BELGraph source:
    :param pybel.BELGraph target:
    """
    target.namespace_url.update(source.graph.get(GRAPH_NAMESPACE_URL, {}))
    target.namespace_pattern.update(source.graph.get(GRAPH_NAMESPACE_PATTERN, {}))

    target.annotation_url.update(source.graph.get(GRAPH_ANNOTATION_URL, {}))
    target.annotation_pattern.update(source.graph.get(GRAPH_ANNOTATION_PATTERN, {}))
    for keyword, values in source.graph.get(GRAPH_ANNOTATION_LIST, {}).items():
        if keyword not in target.annotation_list:
            target.annotation_list[keyword] = values
        else:
            target.annotation_list[keyword].update(values)
