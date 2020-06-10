# -*- coding: utf-8 -*-

"""Functions for inducing graphs by nodes and by edge filters."""

from typing import Iterable, Optional

import networkx as nx

from ..utils import expand_by_edge_filter
from ...filters.edge_predicates import is_causal_relation
from ...filters.node_filters import filter_nodes
from ...filters.typing import EdgePredicates, NodePredicates
from ...operations import subgraph
from ...pipeline import transformation
from ....dsl import BaseEntity

__all__ = [
    'get_subgraph_by_edge_filter',
    'get_subgraph_by_induction',
    'get_subgraph_by_node_filter',
    'get_largest_component',
    'get_causal_subgraph',
]


@transformation
def get_subgraph_by_edge_filter(graph, edge_predicates: Optional[EdgePredicates] = None):
    """Induce a sub-graph on all edges that pass the given filters.

    :param pybel.BELGraph graph: A BEL graph
    :param edge_predicates: An edge predicate or list of edge predicates
    :return: A BEL sub-graph induced over the edges passing the given filters
    :rtype: pybel.BELGraph
    """
    rv = graph.__class__()
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


@transformation
def get_subgraph_by_node_filter(graph, node_predicates: NodePredicates):
    """Induce a sub-graph on the nodes that pass the given predicate(s).

    :param pybel.BELGraph graph: A BEL graph
    :param node_predicates: A node predicate or list of node predicates
    :rtype: pybel.BELGraph
    """
    return get_subgraph_by_induction(graph, filter_nodes(graph, node_predicates))


@transformation
def get_largest_component(graph):
    """Get the giant component of a graph.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: pybel.BELGraph
    """
    biggest_component_nodes = max(nx.weakly_connected_components(graph), key=len)
    return subgraph(graph, biggest_component_nodes)


@transformation
def get_causal_subgraph(graph):
    """Build a new sub-graph induced over the causal edges.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: pybel.BELGraph
    """
    return get_subgraph_by_edge_filter(graph, is_causal_relation)
