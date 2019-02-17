# -*- coding: utf-8 -*-

"""Summary functions for nodes in BEL graphs."""

import itertools as itt
from collections import Counter, defaultdict
from typing import List, Optional, Tuple

from ..filters.node_predicates import has_variant
from ...constants import (
    ACTIVITY, EFFECT, FROM_LOC, FUSION, IDENTIFIER, KIND, LOCATION, MEMBERS, MODIFIER, NAME, NAMESPACE,
    OBJECT, PARTNER_3P, PARTNER_5P, SUBJECT, TO_LOC, TRANSLOCATION, VARIANTS,
)
from ...dsl import BaseEntity, Pathology

__all__ = [
    'get_functions',
    'count_functions',
    'count_namespaces',
    'get_namespaces',
    'count_names_by_namespace',
    'get_names_by_namespace',
    'get_unused_namespaces',
    'count_variants',
    'get_names',
    'count_pathologies',
    'get_top_pathologies',
    'get_top_hubs',
]


def _function_iterator(graph):
    """Iterate over the functions in a graph.

    :rtype: iter[str]
    """
    return (
        node.function
        for node in graph
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
        node[NAMESPACE]
        for node in graph
        if NAMESPACE in node
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


def get_names(graph):
    """Get all names for each namespace.

    :type graph: pybel.BELGraph
    :rtype: dict[str,set[str]]
    """
    rv = defaultdict(set)
    for namespace, name in _identifier_filtered_iterator(graph):
        rv[namespace].add(name)
    return dict(rv)


def _identifier_filtered_iterator(graph):
    """Iterate over names in the given namespace."""
    for data in graph:
        for pair in _get_node_names(data):
            yield pair

        for member in data.get(MEMBERS, []):
            for pair in _get_node_names(member):
                yield pair

    for ((_, _, data), side) in itt.product(graph.edges(data=True), (SUBJECT, OBJECT)):
        side_data = data.get(side)
        if side_data is None:
            continue

        modifier = side_data.get(MODIFIER)
        effect = side_data.get(EFFECT)

        if modifier == ACTIVITY and effect is not None and NAMESPACE in effect and NAME in effect:
            yield effect[NAMESPACE], effect[NAME]

        elif modifier == TRANSLOCATION and effect is not None:
            from_loc = effect.get(FROM_LOC)
            if NAMESPACE in from_loc and NAME in from_loc:
                yield from_loc[NAMESPACE], from_loc[NAME]

            to_loc = effect.get(TO_LOC)
            if NAMESPACE in to_loc and NAME in to_loc:
                yield to_loc[NAMESPACE], to_loc[NAME]

        location = side_data.get(LOCATION)
        if location is not None and NAMESPACE in location and NAME in location:
            yield location[NAMESPACE], location[NAME]


def _get_node_names(data):
    if NAMESPACE in data:
        yield data[NAMESPACE], data[NAME]

    elif FUSION in data:
        yield data[FUSION][PARTNER_3P][NAMESPACE], data[FUSION][PARTNER_3P][NAME]
        yield data[FUSION][PARTNER_5P][NAMESPACE], data[FUSION][PARTNER_5P][NAME]

    if VARIANTS in data:
        for variant in data[VARIANTS]:
            identifier = variant.get(IDENTIFIER)
            if identifier is not None and NAMESPACE in identifier and NAME in identifier:
                yield identifier[NAMESPACE], identifier[NAME]


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
        for data in graph
        if has_variant(graph, data)
        for variant_data in data[VARIANTS]
    )


def get_top_hubs(graph, *, n: Optional[int] = 15) -> List[Tuple[BaseEntity, int]]:
    """Get the top hubs in the graph by BEL.

    :param pybel.BELGraph graph: A BEL graph
    :param n: The number of top hubs to return. If None, returns all nodes
    """
    return Counter(dict(graph.degree())).most_common(n=n)


def _pathology_iterator(graph):
    """Iterate over edges in which either the source or target is a pathology node.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: iter
    """
    for node in itt.chain.from_iterable(graph.edges()):
        if isinstance(node, Pathology):
            yield node


def count_pathologies(graph):
    """Count the number of edges in which each pathology is incident.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: Counter
    """
    return Counter(_pathology_iterator(graph))


def get_top_pathologies(graph, n: Optional[int] = 15) -> List[Tuple[BaseEntity, int]]:
    """Get the top highest relationship-having edges in the graph by BEL.

    :param pybel.BELGraph graph: A BEL graph
    :param n: The number of top connected pathologies to return. If None, returns all nodes
    """
    return count_pathologies(graph).most_common(n)
