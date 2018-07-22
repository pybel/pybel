# -*- coding: utf-8 -*-

"""Functions for inducing random sub-graphs."""

import bisect
import logging
import random

__all__ = [
    'get_graph_with_random_edges',
]

log = logging.getLogger(__name__)


def _random_edge_iterator(graph, n_edges):
    """Get a random set of edges from the graph and randomly samples a key from each.

    :type graph: pybel.BELGraph
    :param int n_edges: Number of edges to randomly select from the given graph
    :rtype: iter[tuple[tuple,tuple,int,dict]]
    """
    universe_edges = graph.edges()
    random.shuffle(universe_edges)

    for u, v in universe_edges[:n_edges]:
        keys = list(graph[u][v])
        k = random.choice(keys)
        yield u, v, k, graph[u][v][k]


def get_graph_with_random_edges(graph, n_edges):
    """Build a new graph from a seeding of edges.

    :type graph: pybel.BELGraph
    :param int n_edges: Number of edges to randomly select from the given graph
    :rtype: pybel.BELGraph
    """
    result = graph.fresh_copy()

    result.add_edges_from(
        (
            (u, v, k, d)
            if k < 0 else
            (u, v, d)
        )
        for u, v, k, d in _random_edge_iterator(graph, n_edges)
    )

    return result


class WeightedRandomGenerator(object):
    """A weighted random nmber generator,"""

    def __init__(self, weights):
        self.totals = []
        weight_total = 0

        for weight in weights:
            weight_total += weight
            self.totals.append(weight_total)

    def next(self):
        """Get a random index."""
        rnd = random.random() * self.totals[-1]
        return bisect.bisect_right(self.totals, rnd)


def get_random_node(graph, node_blacklist):
    """Choose a node from the graph with probabilities based on their degrees

    :type graph: networkx.Graph
    :param set[tuple] node_blacklist: Nodes to filter out
    :rtype: Optional[tuple]
    """
    try:
        nodes, degrees = zip(*(
            (node, degree)
            for node, degree in graph.degree_iter()
            if node not in node_blacklist
        ))
    except ValueError:  # something wrong with graph, probably no elements in graph.degree_iter
        return

    normalized_degrees = [
        degree / (2 * graph.number_of_edges())
        for degree in degrees
    ]

    wrg = WeightedRandomGenerator(normalized_degrees)

    return nodes[wrg.next()]
