# -*- coding: utf-8 -*-

from ..utils import expand_by_edge_filter
from ...pipeline import transformation

__all__ = [
    'get_subgraph_by_edge_filter',
    'get_subgraph_by_induction',
]


@transformation
def get_subgraph_by_edge_filter(graph, edge_predicates=None):
    """Induce a sub-graph on all edges that pass the given filters.

    :param pybel.BELGraph graph: A BEL graph
    :param edge_predicates: An edge predicate or list of edge predicates
    :type edge_predicates: None or ((pybel.BELGraph, tuple, tuple, int) -> bool) or iter[(pybel.BELGraph, tuple, tuple, int) -> bool]
    :return: A BEL sub-graph induced over the edges passing the given filters
    :rtype: pybel.BELGraph
    """
    rv = graph.fresh_copy()
    expand_by_edge_filter(graph, rv, edge_predicates=edge_predicates)
    return rv


@transformation
def get_subgraph_by_induction(graph, nodes):
    """Induce a sub-graph over the given nodes or return None if none of the nodes are in the given graph.

    :param pybel.BELGraph graph: A BEL graph
    :param iter[tuple] nodes: A list of BEL nodes in the graph
    :rtype: Optional[pybel.BELGraph]
    """
    if all(node not in graph for node in nodes):
        return

    return graph.subgraph(nodes)
