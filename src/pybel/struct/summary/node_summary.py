# -*- coding: utf-8 -*-

"""Summary functions for nodes in BEL graphs."""

import itertools as itt
import typing
from collections import Counter, defaultdict
from typing import Any, Iterable, List, Mapping, Optional, Set, Tuple

from ..filters import get_nodes, has_activity, has_variant, is_degraded, is_translocated
from ..graph import BELGraph
from ...constants import (
    ACTIVITY, CONCEPT, EFFECT, FROM_LOC, FUSION, KIND, LOCATION, MEMBERS, MODIFIER, NAME, NAMESPACE, PARTNER_3P,
    PARTNER_5P, SOURCE_MODIFIER, TARGET_MODIFIER, TO_LOC, TRANSLOCATION, VARIANTS,
)
from ...dsl import BaseConcept, BaseEntity, CentralDogma, EntityVariant, FusionBase, ListAbundance, Pathology, Reaction
from ...language import Entity

__all__ = [
    'get_functions',
    'count_functions',
    'get_namespaces',
    'count_namespaces',
    'get_unused_namespaces',
    'count_names_by_namespace',
    'get_names',
    'get_names_by_namespace',
    'iterate_node_entities',
    'iterate_entities',
    'node_is_grounded',
    'get_ungrounded_nodes',
    'count_variants',
    'count_pathologies',
    'get_top_pathologies',
    'get_top_hubs',
]


def _function_iterator(graph: BELGraph) -> Iterable[str]:
    """Iterate over the functions in a graph.

    :param graph: A BEL graph
    """
    return (
        node.function
        for node in graph
    )


def get_functions(graph: BELGraph) -> Set[str]:
    """Get the set of all functions used in this graph.

    :param graph: A BEL graph
    :return: A set of functions
    """
    return set(_function_iterator(graph))


def count_functions(graph: BELGraph) -> typing.Counter[str]:
    """Count the frequency of each function present in a graph.

    :param graph: A BEL graph
    :return: A Counter from {function: frequency}
    """
    return Counter(_function_iterator(graph))


def _iterate_namespaces(graph: BELGraph) -> Iterable[str]:
    """Iterate over all namespaces found in the graph.

    :param graph: A BEL graph
    """
    for entity in itt.chain(iterate_entities(graph), _iterate_edge_entities(graph)):
        yield entity.namespace


def _iterate_edge_entities(graph: BELGraph) -> Iterable[Entity]:
    for ((_, _, data), side) in itt.product(graph.edges(data=True), (SOURCE_MODIFIER, TARGET_MODIFIER)):
        side_data = data.get(side)
        if side_data is None:
            continue

        modifier = side_data.get(MODIFIER)
        effect = side_data.get(EFFECT)

        if modifier == ACTIVITY and effect is not None:
            assert isinstance(effect, Entity)
            yield effect
        elif modifier == TRANSLOCATION and effect is not None:
            from_loc = effect[FROM_LOC]
            assert isinstance(from_loc, Entity)
            yield from_loc
            to_loc = effect[TO_LOC]
            assert isinstance(to_loc, Entity)
            yield to_loc

        location = side_data.get(LOCATION)
        if location is not None:
            assert isinstance(location, Entity)
            yield location


def count_namespaces(graph: BELGraph) -> typing.Counter[str]:
    """Count the frequency of each namespace across all nodes (that have namespaces).

    :param graph: A BEL graph
    :return: A Counter from {namespace: frequency}
    """
    return Counter(_iterate_namespaces(graph))


def get_namespaces(graph: BELGraph) -> Set[str]:
    """Get the set of all namespaces used in this graph.

    :param graph: A BEL graph
    :return: A set of namespaces
    """
    return set(_iterate_namespaces(graph))


def get_unused_namespaces(graph: BELGraph) -> Set[str]:
    """Get the set of all namespaces that are defined in a graph, but are never used.

    :param graph: A BEL graph
    :return: A set of namespaces that are included but not used
    """
    return graph.defined_namespace_keywords - get_namespaces(graph)


def get_names(graph: BELGraph) -> Mapping[str, Set[str]]:
    """Get all names for each namespace.

    :param graph: A BEL graph
    """
    rv = defaultdict(set)
    for namespace, name in _identifier_filtered_iterator(graph):
        rv[namespace].add(name)
    return dict(rv)


def iterate_entities(graph: BELGraph) -> Iterable[Entity]:
    """Iterate over all entities in the graph.

    :param graph: A BEL graph
    """
    for node in graph:
        yield from iterate_node_entities(node)


def iterate_node_entities(node: BaseEntity) -> Iterable[Entity]:
    """Iterate over all named entities that comprise a node.

    This includes the node's name, the members/reactants/products of the node,
    the fusion partners, the named variants, and all recursive ones too.

    :param node: A BEL node

    Entities in a simple protein:

    >>> from pybel.dsl import Protein
    >>> from pybel.language import Entity
    >>> from pybel.struct.summary import iterate_entities
    >>> protein = Protein(namespace='hgnc', identifier='1455', name='CALR')
    >>> protein_entities = list(iterate_node_entities(protein))
    >>> assert [Entity(namespace='hgnc', identifier='1455', name='CALR')] == protein_entities

    Entities in a protein complex:

    >>> from pybel.dsl import Protein, ComplexAbundance
    >>> from pybel.language import Entity
    >>> from pybel.struct.summary import iterate_entities
    >>> protein_1 = Protein(namespace='hgnc', identifier='1')
    >>> protein_2 = Protein(namespace='hgnc', identifier='2')
    >>> complex_1 = ComplexAbundance([protein_1, protein_2])
    >>> complex_entities = list(iterate_node_entities(complex_1))
    >>> assert [Entity(namespace='hgnc', identifier='1'), Entity(namespace='hgnc', identifier='2')] == complex_entities
    """
    if isinstance(node, BaseConcept):
        yield node.entity
    if isinstance(node, ListAbundance):
        for member in node.members:
            yield from iterate_node_entities(member)
    if isinstance(node, Reaction):
        for member in itt.chain(node.reactants, node.products):
            yield from iterate_node_entities(member)
    if isinstance(node, CentralDogma):
        for variant in node.variants or []:
            if isinstance(variant, EntityVariant):
                yield variant.entity
    if isinstance(node, FusionBase):
        yield from iterate_node_entities(node.partner_5p)
        yield from iterate_node_entities(node.partner_3p)


def _identifier_filtered_iterator(graph) -> Iterable[Tuple[str, str]]:
    """Iterate over names in the given namespace."""
    for data in graph:
        for pair in _get_node_names(data):
            yield pair

        for member in data.get(MEMBERS, []):
            for pair in _get_node_names(member):
                yield pair

    for ((_, _, data), side) in itt.product(graph.edges(data=True), (SOURCE_MODIFIER, TARGET_MODIFIER)):
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


def _get_node_names(data: Mapping[str, Any]) -> Iterable[Tuple[str, str]]:
    if CONCEPT in data:
        yield data[CONCEPT][NAMESPACE], data[CONCEPT][NAME]

    elif FUSION in data:
        partner_5p_concept = data[FUSION][PARTNER_5P][CONCEPT]
        partner_3p_concept = data[FUSION][PARTNER_3P][CONCEPT]
        yield partner_5p_concept[NAMESPACE], partner_5p_concept[NAME]
        yield partner_3p_concept[NAMESPACE], partner_3p_concept[NAME]

    if VARIANTS in data:
        for variant in data[VARIANTS]:
            concept = variant.get(CONCEPT)
            if concept is not None and NAMESPACE in concept and NAME in concept:
                yield concept[NAMESPACE], concept[NAME]


def _namespace_filtered_iterator(graph: BELGraph, namespace: str) -> Iterable[str]:
    """Iterate over names in the given namespace.

    :param graph: A BEL graph
    :param namespace: A namespace prefix
    """
    for it_namespace, name in _identifier_filtered_iterator(graph):
        if namespace == it_namespace:
            yield name


def count_names_by_namespace(graph: BELGraph, namespace: str) -> typing.Counter[str]:
    """Get the set of all of the names in a given namespace that are in the graph.

    :param graph: A BEL graph
    :param namespace: A namespace prefix
    :return: A counter from {name: frequency}

    :raises IndexError: if the namespace is not defined in the graph.
    """
    if namespace not in graph.defined_namespace_keywords:
        raise IndexError('{} is not defined in {}'.format(namespace, graph))

    return Counter(_namespace_filtered_iterator(graph, namespace))


def get_names_by_namespace(graph: BELGraph, namespace: str) -> Set[str]:
    """Get the set of all of the names in a given namespace that are in the graph.

    :param pybel.BELGraph graph: A BEL graph
    :param namespace: A namespace prefix
    :return: A set of names belonging to the given namespace that are in the given graph

    :raises IndexError: if the namespace is not defined in the graph.
    """
    if namespace not in graph.defined_namespace_keywords:
        raise IndexError('{} is not defined in {}'.format(namespace, graph))

    return set(_namespace_filtered_iterator(graph, namespace))


def count_variants(graph: BELGraph) -> typing.Counter[str]:
    """Count how many of each type of variant a graph has.

    :param graph: A BEL graph
    """
    return Counter(
        variant_data[KIND]
        for data in graph
        if has_variant(graph, data)
        for variant_data in data[VARIANTS]
    )


def get_top_hubs(graph: BELGraph, *, n: Optional[int] = 15) -> List[Tuple[BaseEntity, int]]:
    """Get the top hubs in the graph by BEL.

    :param graph: A BEL graph
    :param n: The number of top hubs to return. If None, returns all nodes
    """
    return Counter(dict(graph.degree())).most_common(n=n)


def count_pathologies(graph: BELGraph) -> typing.Counter[BaseEntity]:
    """Count the number of edges in which each pathology is incident.

    :param graph: A BEL graph
    """
    # Don't double count relationships
    edges = {tuple(sorted([u, v], key=lambda node: node.as_bel())) for u, v in graph.edges()}
    return Counter(
        node
        for node in itt.chain.from_iterable(edges)
        if isinstance(node, Pathology)
    )


def get_top_pathologies(graph: BELGraph, n: Optional[int] = 15) -> List[Tuple[BaseEntity, int]]:
    """Get the top highest relationship-having edges in the graph by BEL.

    :param graph: A BEL graph
    :param n: The number of top connected pathologies to return. If None, returns all nodes
    """
    return count_pathologies(graph).most_common(n)


def get_ungrounded_nodes(graph: BELGraph) -> Set[BaseEntity]:
    """Get all ungrounded nodes in the graph.

    :param graph: A BEL graph
    """
    return {
        node
        for node in graph
        if not node_is_grounded(node)
    }


def node_is_grounded(node: BaseEntity) -> bool:
    """Check if a node is grounded.

    :param node: A BEL node
    """
    return all(
        entity.identifier is not None and entity.name is not None
        for entity in iterate_node_entities(node)
    )


def get_degradations(graph: BELGraph) -> Set[BaseEntity]:
    """Get all nodes that are degraded."""
    return get_nodes(graph, is_degraded)


def get_activities(graph: BELGraph) -> Set[BaseEntity]:
    """Get all nodes that have molecular activities."""
    return get_nodes(graph, has_activity)


def get_translocated(graph: BELGraph) -> Set[BaseEntity]:
    """Get all nodes that are translocated."""
    return get_nodes(graph, is_translocated)


def count_modifications(graph: BELGraph) -> Counter:
    """Get a modifications count dictionary."""
    return Counter(remove_falsy_values({
        'Translocations': len(get_translocated(graph)),
        'Degradations': len(get_degradations(graph)),
        'Molecular Activities': len(get_activities(graph)),
    }))


def remove_falsy_values(counter: Mapping[Any, int]) -> Mapping[Any, int]:
    """Remove all values that are zero."""
    return {
        label: count
        for label, count in counter.items()
        if count
    }
