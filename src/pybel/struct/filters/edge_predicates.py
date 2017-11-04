# -*- coding: utf-8 -*-

from ...constants import CITATION, CITATION_TYPE, CITATION_TYPE_PUBMED

__all__ = [
    'edge_data_has_pubmed_citation',
    'edge_has_pubmed_citation',
]


def keep_edge_permissive(graph, u, v, k, d):
    """Passes for all edges

    :param BELGraph graph: A BEL Graph
    :param tuple u: A BEL node
    :param tuple v: A BEL node
    :param int k: The edge key between the given nodes
    :param dict d: The edge data dictionary
    :return: Always returns :code:`True`
    :rtype: bool
    """
    return True


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


def edge_has_provenance(graph, u, v, k, d):
    """Passes for edges with provenance information (i.e. citation and evidence)

    :param BELGraph graph: A BEL Graph
    :param tuple u: A BEL node
    :param tuple v: A BEL node
    :param int k: The edge key between the given nodes
    :param dict d: The edge data dictionary
    :return: If the edge has both a citation and and evidence entry
    :rtype: bool
    """
    return graph.has_edge_citation(u, v, k) and graph.has_edge_evidence(u, v, k)
