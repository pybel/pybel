# -*- coding: utf-8 -*-

"""This module contains functions that provide summaries of the nodes in a graph."""

from collections import Counter

from ..filters.node_predicates import has_variant
from ...constants import FUNCTION, FUSION, KIND, NAME, NAMESPACE, PARTNER_3P, PARTNER_5P, VARIANTS

__all__ = [
    'get_functions',
    'count_functions',
    'count_namespaces',
    'get_namespaces',
    'count_names_by_namespace',
    'get_names_by_namespace',
    'get_unused_namespaces',
    'count_variants',
]


def _function_iterator(graph):
    """Iterate over the functions in a graph."""
    return (
        data[FUNCTION]
        for _, data in graph.nodes(data=True)
    )


def get_functions(graph):
    """Get the set of all functions used in this graph.

    :param pybel.BELGraph graph: A BEL graph
    :return: A set of functions
    :rtype: set[str]
    """
    return set(_function_iterator(graph))


def count_functions(graph):
    """Count the frequency of each function present in a graph.

    :param pybel.BELGraph graph: A BEL graph
    :return: A Counter from {function: frequency}
    :rtype: collections.Counter
    """
    return Counter(_function_iterator(graph))


def _iterate_namespaces(graph):
    return (
        data[NAMESPACE]
        for _, data in graph.nodes(data=True)
        if NAMESPACE in data
    )


def count_namespaces(graph):
    """Count the frequency of each namespace across all nodes (that have namespaces).

    :param pybel.BELGraph graph: A BEL graph
    :return: A Counter from {namespace: frequency}
    :rtype: collections.Counter
    """
    return Counter(_iterate_namespaces(graph))


def get_namespaces(graph):
    """Get the set of all namespaces used in this graph.

    :param pybel.BELGraph graph: A BEL graph
    :return: A set of namespaces
    :rtype: set[str]
    """
    return set(_iterate_namespaces(graph))


def get_unused_namespaces(graph):
    """Get the set of all namespaces that are defined in a graph, but are never used.

    :param pybel.BELGraph graph: A BEL graph
    :return: A set of namespaces that are included but not used
    :rtype: set[str]
    """
    return graph.defined_namespace_keywords - get_namespaces(graph)


def _identifier_filtered_iterator(graph):
    """Iterate over names in the given namespace."""
    for _, data in graph.nodes(data=True):
        if NAMESPACE in data:
            yield data[NAMESPACE], data[NAME]

        elif FUSION in data:
            yield data[FUSION][PARTNER_3P][NAMESPACE], data[FUSION][PARTNER_3P][NAME]
            yield data[FUSION][PARTNER_5P][NAMESPACE], data[FUSION][PARTNER_5P][NAME]


def _namespace_filtered_iterator(graph, namespace):
    """Iterate over names in the given namespace."""
    for it_namespace, name in _identifier_filtered_iterator(graph):
        if namespace == it_namespace:
            yield name


def count_names_by_namespace(graph, namespace):
    """Get the set of all of the names in a given namespace that are in the graph.

    :param pybel.BELGraph graph: A BEL graph
    :param str namespace: A namespace keyword
    :return: A counter from {name: frequency}
    :rtype: collections.Counter

    :raises IndexError: if the namespace is not defined in the graph.
    """
    if namespace not in graph.defined_namespace_keywords:
        raise IndexError('{} is not defined in {}'.format(namespace, graph))

    return Counter(_namespace_filtered_iterator(graph, namespace))


def get_names_by_namespace(graph, namespace):
    """Get the set of all of the names in a given namespace that are in the graph.

    :param pybel.BELGraph graph: A BEL graph
    :param str namespace: A namespace keyword
    :return: A set of names belonging to the given namespace that are in the given graph
    :rtype: set[str]

    :raises IndexError: if the namespace is not defined in the graph.
    """
    if namespace not in graph.defined_namespace_keywords:
        raise IndexError('{} is not defined in {}'.format(namespace, graph))

    return set(_namespace_filtered_iterator(graph, namespace))


def count_variants(graph):
    """Count how many of each type of variant a graph has.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: Counter
    """
    return Counter(
        variant_data[KIND]
        for node, data in graph.nodes(data=True)
        if has_variant(graph, node)
        for variant_data in data[VARIANTS]
    )
