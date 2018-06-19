# -*- coding: utf-8 -*-

"""Utilities for PyBEL testing."""

import itertools as itt
import random

from pybel import BELGraph
from pybel.constants import INCREASES
from pybel.dsl import protein
from pybel.testing.utils import n

__all__ = [
    'generate_random_graph',
]


def generate_random_graph(n_nodes, n_edges):
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
        graph.add_qualified_edge(
            u, v,
            relation=INCREASES,
            citation=n(),
            evidence=n(),
        )

    return graph
