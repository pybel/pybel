# -*- coding: utf-8 -*-

"""This module contains functions that provide summaries of the nodes in a graph"""

from collections import Counter

from ...constants import *

__all__ = [
    'get_functions',
    'count_functions',
    'count_namespaces',
    'get_namespaces',
    'get_names_by_namespace',
    'get_unused_namespaces',
]


def _function_iterator(graph):
    """Iterates over the functions in a graph"""
    return (
        data[FUNCTION]
        for _, data in graph.nodes_iter(data=True)
    )


def get_functions(graph):
    """Gets the set of all functions used in this graph

    :param pybel.BELGraph graph: A BEL graph
    :return: A set of functions
    :rtype: set[str]
    """
    return set(_function_iterator(graph))


def count_functions(graph):
    """Counts the frequency of each function present in a graph

    :param pybel.BELGraph graph: A BEL graph
    :return: A Counter from {function: frequency}
    :rtype: collections.Counter
    """
    return Counter(_function_iterator(graph))


def _iterate_namespaces(graph):
    return (
        data[NAMESPACE]
        for _, data in graph.nodes_iter(data=True)
        if NAMESPACE in data
    )


def count_namespaces(graph):
    """Counts the frequency of each namespace across all nodes (that have namespaces)

    :param pybel.BELGraph graph: A BEL graph
    :return: A Counter from {namespace: frequency}
    :rtype: collections.Counter
    """
    return Counter(_iterate_namespaces(graph))


def get_namespaces(graph):
    """Gets the set of all namespaces used in this graph

    :param pybel.BELGraph graph: A BEL graph
    :return: A set of namespaces
    :rtype: set[str]
    """
    return set(_iterate_namespaces(graph))


def get_unused_namespaces(graph):
    """Gets the set of all namespaces that are defined in a graph, but are never used.

    :param pybel.BELGraph graph: A BEL graph
    :return: A set of namespaces that are included but not used
    :rtype: set[str]
    """
    return graph.defined_namespace_keywords - get_namespaces(graph)


def _identifier_filtered_iterator(graph):
    """Iterates over names in the given namespace"""
    for _, data in graph.nodes_iter(data=True):
        if NAMESPACE in data:
            yield data[NAMESPACE], data[NAME]

        elif FUSION in data:
            yield data[FUSION][PARTNER_3P][NAMESPACE], data[FUSION][PARTNER_3P][NAME]
            yield data[FUSION][PARTNER_5P][NAMESPACE], data[FUSION][PARTNER_5P][NAME]


def _namespace_filtered_iterator(graph, namespace):
    """Iterates over names in the given namespace"""
    for it_namespace, name in _identifier_filtered_iterator(graph):
        if namespace == it_namespace:
            yield name


def count_names_by_namespace(graph, namespace):
    """Get the set of all of the names in a given namespace that are in the graph. Raises :data:`IndexError` if the
    namespace is not defined in the graph.

    :param pybel.BELGraph graph: A BEL graph
    :param str namespace: A namespace keyword
    :return: A counter from {name: frequency}
    :rtype: collections.Counter
    """
    if namespace not in graph.defined_namespace_keywords:
        raise IndexError('{} is not defined in {}'.format(namespace, graph))

    return Counter(_namespace_filtered_iterator(graph, namespace))


def get_names_by_namespace(graph, namespace):
    """Get the set of all of the names in a given namespace that are in the graph. Raises :data:`IndexError` if the
    namespace is not defined in the graph.

    :param pybel.BELGraph graph: A BEL graph
    :param str namespace: A namespace keyword
    :return: A set of names belonging to the given namespace that are in the given graph
    :rtype: set[str]
    """
    if namespace not in graph.defined_namespace_keywords:
        raise IndexError('{} is not defined in {}'.format(namespace, graph))

    return set(_namespace_filtered_iterator(graph, namespace))
