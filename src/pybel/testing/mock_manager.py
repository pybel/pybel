# -*- coding: utf-8 -*-

"""Mocks for PyBEL testing."""

from typing import Iterable

from ..manager.models import Network
from ..struct import union


class MockQueryManager:
    """A mock manager."""

    def __init__(self, graphs=None):
        """Build a mock manager appropriate for testing the pipeline and query builders.

        :param Optional[list[pybel.BELGraph]] graphs: A list of BEL graphs to index
        """
        self.graphs = []

        #: A lookup for nodes from the node hash (string) to the node tuple
        self.hash_to_node = {}

        #: A lookup from network identifier to graph
        self.id_graph = {}

        if graphs is not None:
            for graph in graphs:
                self.insert_graph(graph)

    def count_networks(self) -> int:
        """Count networks in the manager."""
        return len(self.graphs)

    def insert_graph(self, graph) -> Network:
        """Insert a graph and ensure its nodes are cached.

        :param pybel.BELGraph graph:
        """
        network_id = len(self.graphs)
        self.graphs.append(graph)
        self.id_graph[network_id] = graph

        for node in graph:
            self.hash_to_node[node.md5] = node

        return Network(id=network_id)

    def get_graph_by_ids(self, network_ids: Iterable[int]):
        """Get a graph from the union of multiple networks.

        :param network_ids: The identifiers of networks in the database
        :rtype: pybel.BELGraph
        """
        network_ids = list(network_ids)

        if len(network_ids) == 1:
            return self.id_graph[network_ids[0]]

        graphs = [self.id_graph[graph_id] for graph_id in network_ids]

        return union(graphs)

    def get_dsl_by_hash(self, md5: str):
        """Get a DSL by its hash.

        :rtype: Optional[BaseEntity]
        """
        return self.hash_to_node.get(md5)
