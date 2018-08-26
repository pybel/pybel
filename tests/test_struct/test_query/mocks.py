# -*- coding: utf-8 -*-

from pybel.manager.models import Network
from pybel.struct import union


class MockNetwork:
    """A mock network."""

    def __init__(self, id):
        """Build a mock network with the given identifier."""
        self.id = id


class MockQueryManager:
    """A mock manager."""

    def __init__(self, graphs=None):
        """Build a mock manager appropriate for testing the pipeline and query builders.

        :param Optional[list[pybel.BELGraph]] graphs: A list of BEL graphs to index
        """
        self.graphs = []

        #: A lookup for nodes from the node hash (string) to the node tuple
        self.hash_to_tuple = {}

        #: A lookup from network identifier to graph
        self.id_graph = {}

        if graphs is not None:
            for graph in graphs:
                self.insert_graph(graph)

    def count_networks(self):
        """Count networks in the manager.

        :rtype: int
        """
        return len(self.graphs)

    def insert_graph(self, graph):
        """Insert a graph.

        :param pybel.BELGraph graph:
        :rtype: Network
        """
        network_id = len(self.graphs)
        self.graphs.append(graph)
        self.id_graph[network_id] = graph

        for node, data in graph.nodes(data=True):
            self.hash_to_tuple[data.sha512] = node

        return MockNetwork(id=network_id)

    def get_graph_by_ids(self, network_ids):
        """Get a graph from the union of multiple networks.

        :param iter[int] network_ids: The identifiers of networks in the database
        :rtype: pybel.BELGraph
        """
        network_ids = list(network_ids)

        if len(network_ids) == 1:
            return self.id_graph[network_ids[0]]

        graphs = [
            self.id_graph[graph_id]
            for graph_id in network_ids
        ]

        return union(graphs)
