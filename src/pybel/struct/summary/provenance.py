# -*- coding: utf-8 -*-

from ..filters.edge_predicates import has_pubmed
from ...constants import CITATION, CITATION_REFERENCE

__all__ = [
    'iterate_pubmed_identifiers',
    'get_pubmed_identifiers',
]


def iterate_pubmed_identifiers(graph):
    """Iterate over all PubMed identifiers in a graph.

    :param pybel.BELGraph graph: A BEL graph
    :return: An iterator over the PubMed identifiers in the graph
    :rtype: iter[str]
    """
    return (
        data[CITATION][CITATION_REFERENCE].strip()
        for _, _, data in graph.edges(data=True)
        if has_pubmed(data)
    )


def get_pubmed_identifiers(graph):
    """Get the set of all PubMed identifiers cited in the construction of a graph.

    :param pybel.BELGraph graph: A BEL graph
    :return: A set of all PubMed identifiers cited in the construction of this graph
    :rtype: set[str]
    """
    return set(iterate_pubmed_identifiers(graph))
