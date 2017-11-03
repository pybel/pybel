# -*- coding: utf-8 -*-

from ...constants import CITATION, CITATION_TYPE, CITATION_TYPE_PUBMED

__all__ = [
    'edge_data_has_pubmed_citation',
    'edge_has_pubmed_citation',
]


def edge_data_has_pubmed_citation(data):
    """Checks if the edge data dictionary has a PubMed citation

    :param dict data: A PyBEL edge data dictionary from a :class:`pybel.BELGraph`
    :return: Does the edge data dictionary has a PubMed citation?
    :rtype: bool
    """
    return CITATION in data and CITATION_TYPE_PUBMED == data[CITATION][CITATION_TYPE]


def edge_has_pubmed_citation(graph, u, v, k, data):
    """Passes for edges that have PubMed citations

    :param pybel.BELGraph graph: A BEL Graph
    :param tuple u: A BEL node
    :param tuple v: A BEL node
    :param int k: The edge key between the given nodes
    :param dict data: The edge data dictionary
    :return: Is the edge's citation from :data:`PUBMED`?
    :rtype: bool
    """
    return edge_data_has_pubmed_citation(data)
