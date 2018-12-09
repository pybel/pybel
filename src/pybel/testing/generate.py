# -*- coding: utf-8 -*-

"""Utilities for PyBEL testing."""

import itertools as itt
import random

from .utils import n
from ..dsl import protein
from ..struct import BELGraph

__all__ = [
    'generate_random_graph',
]


def generate_random_graph(n_nodes, n_edges, namespace='NS'):
    """Generate a sub-graph with random nodes and edges.

    :param int n_nodes: Number of nodes to make
    :param int n_edges: Number of edges to make
    :param str namespace: The namespace of the nodes to use
    :rtype: pybel.BELGraph
    """
    graph = BELGraph()

    nodes = [
        protein(namespace=namespace, name=str(i))
        for i in range(1, n_nodes)
    ]

    edges = list(itt.combinations(nodes, r=2))
    edge_sample = random.sample(edges, n_edges)

    for u, v in edge_sample:
        graph.add_increases(u, v, citation=n(), evidence=n())

    return graph
