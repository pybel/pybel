# -*- coding: utf-8 -*-

"""Summary functions for citation and provenance information in BEL graphs."""

import warnings
from typing import Iterable, Set

from ..filters.edge_predicates import has_pubmed
from ...constants import CITATION, CITATION_REFERENCE

__all__ = [
    'iterate_pubmed_identifiers',
    'get_pubmed_identifiers',
    'count_citations',
]


def iterate_pubmed_identifiers(graph) -> Iterable[str]:
    """Iterate over all PubMed identifiers in a graph.

    :param pybel.BELGraph graph: A BEL graph
    :return: An iterator over the PubMed identifiers in the graph
    """
    return (
        data[CITATION][CITATION_REFERENCE].strip()
        for _, _, data in graph.edges(data=True)
        if has_pubmed(data)
    )


def get_pubmed_identifiers(graph) -> Set[str]:
    """Get the set of all PubMed identifiers cited in the construction of a graph.

    :param pybel.BELGraph graph: A BEL graph
    :return: A set of all PubMed identifiers cited in the construction of this graph
    """
    return set(iterate_pubmed_identifiers(graph))


def count_citations(graph) -> int:
    """Return the number of unique citations.

    :param pybel.BELGraph graph: A BEL graph
    :return: The number of unique citations in the graph.
    """
    warnings.warn('use graph.number_of_citations()', DeprecationWarning)
    return graph.number_of_citations()
