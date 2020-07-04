# -*- coding: utf-8 -*-

"""Summary functions for citation and provenance information in BEL graphs."""

from typing import Iterable, Set

from ..filters.edge_predicates import has_pubmed
from ..graph import BELGraph
from ...constants import CITATION, IDENTIFIER

__all__ = [
    'iterate_pubmed_identifiers',
    'get_pubmed_identifiers',
]


def iterate_pubmed_identifiers(graph: BELGraph) -> Iterable[str]:
    """Iterate over all PubMed identifiers in a graph.

    :param graph: A BEL graph
    :return: An iterator over the PubMed identifiers in the graph
    """
    return (
        data[CITATION][IDENTIFIER].strip()
        for _, _, data in graph.edges(data=True)
        if has_pubmed(data)
    )


def get_pubmed_identifiers(graph: BELGraph) -> Set[str]:
    """Get the set of all PubMed identifiers cited in the construction of a graph.

    :param graph: A BEL graph
    :return: A set of all PubMed identifiers cited in the construction of this graph
    """
    return set(iterate_pubmed_identifiers(graph))
