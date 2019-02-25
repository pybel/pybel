# -*- coding: utf-8 -*-

"""Functions for inducing graphs by nodes and by edge filters."""

from typing import Iterable, Optional

from ..utils import expand_by_edge_filter
from ...filters.typing import EdgePredicates
from ...operations import subgraph
from ...pipeline import transformation
from ....dsl import BaseEntity

__all__ = [
    'get_subgraph_by_edge_filter',
    'get_subgraph_by_induction',
]


@transformation
def get_subgraph_by_edge_filter(graph, edge_predicates: Optional[EdgePredicates] = None):
    """Induce a sub-graph on all edges that pass the given filters.

    :param pybel.BELGraph graph: A BEL graph
    :param edge_predicates: An edge predicate or list of edge predicates
    :return: A BEL sub-graph induced over the edges passing the given filters
    :rtype: pybel.BELGraph
    """
    rv = graph.fresh_copy()
    expand_by_edge_filter(graph, rv, edge_predicates=edge_predicates)
    return rv


@transformation
def get_subgraph_by_induction(graph, nodes: Iterable[BaseEntity]):
    """Induce a sub-graph over the given nodes or return None if none of the nodes are in the given graph.

    :param pybel.BELGraph graph: A BEL graph
    :param nodes: A list of BEL nodes in the graph
    :rtype: Optional[pybel.BELGraph]
    """
    nodes = tuple(nodes)

    if all(node not in graph for node in nodes):
        return

    return subgraph(graph, nodes)
