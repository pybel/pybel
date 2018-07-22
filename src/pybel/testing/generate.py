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


def generate_random_graph(n_nodes, n_edges, seed=None):
    """Generate a sub-graph with random nodes and edges.

    :param int n_nodes: Number of nodes to make
    :param int n_edges: Number of edges to make
    :rtype: pybel.BELGraph
    """
    graph = BELGraph()

    nodes = [
        protein(namespace='NS', name=str(i))
        for i in range(1, n_nodes)
    ]

    edges = list(itt.combinations(nodes, r=2))
    random.shuffle(edges)

    for u, v in edges[:n_edges]:
        graph.add_increases(u, v, citation=n(), evidence=n())

    return graph
