# -*- coding: utf-8 -*-

"""Utilities for :mod:`pybel.struct`."""

import networkx as nx

__all__ = [
    'update_metadata',
    'update_node_helper',
]


def update_metadata(source, target) -> None:
    """Update the namespace and annotation metadata in the target graph.

    :param pybel.BELGraph source:
    :param pybel.BELGraph target:
    """
    target.namespace_url.update(source.namespace_url)
    target.namespace_pattern.update(source.namespace_pattern)

    target.annotation_url.update(source.annotation_url)
    target.annotation_pattern.update(source.annotation_pattern)
    for keyword, values in source.annotation_list.items():
        if keyword not in target.annotation_list:
            target.annotation_list[keyword] = values
        else:
            target.annotation_list[keyword].update(values)


def update_node_helper(source: nx.Graph, target: nx.Graph) -> None:
    """Update the nodes' data dictionaries in the target graph from the source graph.

    :param source: The universe of all knowledge
    :param target: The target BEL graph
    """
    for node in target:
        if node in source:
            target.nodes[node].update(source.nodes[node])
