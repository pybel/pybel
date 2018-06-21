# -*- coding: utf-8 -*-

from collections import defaultdict

from ..utils import hash_edge

__all__ = [
    'stratify_hash_edges',
    'update_metadata',
    'update_node_helper',
    'ensure_node_from_universe',
]


def stratify_hash_edges(graph):
    """Splits all qualified and unqualified edges by different indexing strategies

    :param BELGraph graph: A BEL network
    :rtype dict[tuple, dict[int, int]], dict[tuple, dict[int, set[int]]]
    """
    qualified_edges = defaultdict(dict)
    unqualified_edges = defaultdict(lambda: defaultdict(set))

    for u, v, k, d in graph.edges_iter(keys=True, data=True):
        hashed_data = hash_edge(u, v, d)

        if k < 0:
            unqualified_edges[u, v][k].add(hashed_data)
        else:
            qualified_edges[u, v][hashed_data] = k

    return dict(qualified_edges), dict(unqualified_edges)


def update_metadata(universe, graph):
    """
    :param pybel.BELGraph graph:
    :param pybel.BELGraph universe:
    """
    graph.namespace_url.update(universe.namespace_url)
    graph.namespace_pattern.update(universe.namespace_pattern)
    graph.annotation_url.update(universe.annotation_url)
    graph.annotation_pattern.update(universe.annotation_pattern)
    graph.annotation_list.update(universe.annotation_list)


def update_node_helper(universe, graph):
    """Update the nodes' data dictionaries from the universe.

    :param nx.Graph universe: The universe of all knowledge
    :param nx.Graph graph: The target BEL graph
    """
    for node in graph:
        if node not in universe:
            continue
        graph.node[node].update(universe.node[node])


def ensure_node_from_universe(universe, graph, node, raise_for_missing=False):
    """Makes sure that the sub-graph has the given node.

    :param pybel.BELGraph universe: The universe of all knowledge
    :param pybel.BELGraph graph: The target BEL graph
    :param tuple node: A BEL node
    :param bool raise_for_missing: Should an error be thrown if the given node is not in the universe?
    """
    if raise_for_missing and node not in universe:
        raise IndexError('{} not in {}'.format(node, universe.name))

    if node not in graph:
        graph.add_node(node, attr_dict=universe.node[node])
