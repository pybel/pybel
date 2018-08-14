# -*- coding: utf-8 -*-

"""Utility functions for grouping sub-graphs."""

from ..utils import update_metadata, update_node_helper

__all__ = [
    'cleanup',
]


def cleanup(graph, subgraphs):
    """Clean up the metadata in the subgraphs.

    :type graph: pybel.BELGraph
    :type subgraphs: dict[Any,pybel.BELGraph]
    """
    for subgraph in subgraphs.values():
        update_node_helper(graph, subgraph)
        update_metadata(graph, subgraph)
