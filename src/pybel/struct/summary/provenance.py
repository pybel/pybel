# -*- coding: utf-8 -*-

"""Summary functions for citation and provenance information in BEL graphs."""

from typing import Iterable, Set

from ..filters.edge_predicates import CITATION_PREDIACATES
from ..graph import BELGraph
from ...constants import CITATION, IDENTIFIER

__all__ = [
    'iterate_pubmed_identifiers',
    'iterate_pmc_identifiers',
    'get_pubmed_identifiers',
    'get_pmc_identifiers',
]


def iterate_citation_identifiers(graph, prefix: str):
    """Iterate over all citation identifiers with the given prefix in a graph.

    :param graph: A BEL graph
    :param prefix: The citation prefix to keep
    :return: An iterator over the PubMed identifiers in the graph
    """
    predicate = CITATION_PREDIACATES.get(prefix)
    if predicate is None:
        raise ValueError(f'Invalid citation prefix: {prefix}')

    return (
        data[CITATION][IDENTIFIER].strip()
        for _, _, data in graph.edges(data=True)
        if predicate(data)
    )


def iterate_pubmed_identifiers(graph: BELGraph) -> Iterable[str]:
    """Iterate over all PubMed identifiers in a graph.

    :param graph: A BEL graph
    :return: An iterator over the PubMed identifiers in the graph
    """
    return iterate_citation_identifiers(graph, 'pubmed')


def iterate_pmc_identifiers(graph: BELGraph) -> Iterable[str]:
    """Iterate over all PMC identifiers in a graph.

    :param graph: A BEL graph
    :return: An iterator over the PMC identifiers in the graph
    """
    return iterate_citation_identifiers(graph, 'pmc')


def get_citation_identifiers(graph: BELGraph, prefix: str) -> Set[str]:
    """Get the set of all identifiers with the give prefix cited in the construction of a graph.

    :param graph: A BEL graph
    :param prefix: The citation prefix to keep
    :return: A set of all PubMed identifiers cited in the construction of this graph
    """
    return set(iterate_citation_identifiers(graph, prefix))


def get_pubmed_identifiers(graph: BELGraph) -> Set[str]:
    """Get the set of all PubMed identifiers cited in the construction of a graph.

    :param graph: A BEL graph
    :return: A set of all PubMed identifiers cited in the construction of this graph
    """
    return get_citation_identifiers(graph, 'pubmed')


def get_pmc_identifiers(graph: BELGraph) -> Set[str]:
    """Get the set of all PMC identifiers cited in the construction of a graph.

    :param graph: A BEL graph
    :return: A set of all PMC identifiers cited in the construction of this graph
    """
    return get_citation_identifiers(graph, 'pmc')
