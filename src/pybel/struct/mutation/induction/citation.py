# -*- coding: utf-8 -*-

"""Induction functions based on provenance information."""

import logging

from .utils import get_subgraph_by_edge_filter
from ...filters.edge_predicate_builders import build_author_inclusion_filter, build_pmid_inclusion_filter
from ...pipeline import transformation

__all__ = [
    'get_subgraph_by_pubmed',
    'get_subgraph_by_authors',
]

log = logging.getLogger(__name__)


@transformation
def get_subgraph_by_pubmed(graph, pubmed_identifiers):
    """Induce a sub-graph over the edges retrieved from the given PubMed identifier(s).

    :param pybel.BELGraph graph: A BEL graph
    :param str or list[str] pubmed_identifiers: A PubMed identifier or list of PubMed identifiers
    :rtype: pybel.BELGraph
    """
    return get_subgraph_by_edge_filter(graph, build_pmid_inclusion_filter(pubmed_identifiers))


@transformation
def get_subgraph_by_authors(graph, authors):
    """Induce a sub-graph over the edges retrieved publications by the given author(s).

    :param pybel.BELGraph graph: A BEL graph
    :param str or list[str] authors: An author or list of authors
    :rtype: pybel.BELGraph
    """
    return get_subgraph_by_edge_filter(graph, build_author_inclusion_filter(authors))
