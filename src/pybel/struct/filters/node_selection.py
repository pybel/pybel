# -*- coding: utf-8 -*-

"""Functions for getting iterables of nodes."""

from .node_filters import get_nodes
from .node_predicate_builders import function_inclusion_filter_builder, namespace_inclusion_builder

__all__ = [
    'get_nodes_by_function',
    'get_nodes_by_namespace',
]


def get_nodes_by_function(graph, func):
    """Get all nodes of a given type.

    :param pybel.BELGraph graph: A BEL graph
    :param func: The BEL function to filter by
    :type func: str or iter[str]
    :return: An iterable of all BEL nodes with the given function
    :rtype: set[BaseEntity]
    """
    return get_nodes(graph, function_inclusion_filter_builder(func))


def get_nodes_by_namespace(graph, namespaces):
    """Get all nodes in the namespace or namespaces.

    :param pybel.BELGraph graph: A BEL graph
    :param namespaces: namespaces to be filtered
    :type namespaces: str or iter[str]
    :rtype: set[BaseEntity]
    """
    return get_nodes(graph, namespace_inclusion_builder(namespaces))
