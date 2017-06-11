# -*- coding: utf-8 -*-



def filter_provenance_edges(graph):
    """Returns an iterator over edges with citation and evidence

    :param BELGraph graph: A BEL network
    :return: An iterator over edges with both a citation and evidence
    :rtype: iter[tuple]
    """
    for u, v, k, d in graph.edges_iter(keys=True, data=True):
        if graph.has_edge_citation(u, v, k) and graph.has_edge_evidence(u, v, k):
            yield u, v, k, d
