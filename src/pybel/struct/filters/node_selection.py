# -*- coding: utf-8 -*-

"""Functions for getting iterables of nodes."""

from .node_filters import filter_nodes
from .node_predicate_builders import function_inclusion_filter_builder

__all__ = [
    'get_nodes_by_function',
]


def get_nodes_by_function(graph, func):
    """Get all nodes of a given type.

    :param pybel.BELGraph graph: A BEL graph
    :param str or iter[str] func: The BEL function to filter by
    :return: An iterable of all BEL nodes with the given function
    :rtype: iter[tuple]
    """
    return filter_nodes(graph, function_inclusion_filter_builder(func))
