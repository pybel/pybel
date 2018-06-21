# -*- coding: utf-8 -*-

__all__ = [
    'update_metadata',
]


def update_metadata(value, graph):
    """
    :param pybel.BELGraph value:
    :param pybel.BELGraph graph:
    """
    value.namespace_url.update(graph.namespace_url)
    value.namespace_pattern.update(graph.namespace_pattern)
    value.annotation_url.update(graph.annotation_url)
    value.annotation_pattern.update(graph.annotation_pattern)
    value.annotation_list.update(graph.annotation_list)
