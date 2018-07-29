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
    """Split all qualified and unqualified edges by different indexing strategies.

    :param BELGraph graph: A BEL network
    :rtype dict[tuple, dict[int, int]], dict[tuple, dict[int, set[int]]]
    """
    qualified_edges = defaultdict(dict)
    unqualified_edges = defaultdict(lambda: defaultdict(set))

    for u, v, k, d in graph.edges(keys=True, data=True):
        hashed_data = hash_edge(u, v, d)

        if k < 0:
            unqualified_edges[u, v][k].add(hashed_data)
        else:
            qualified_edges[u, v][hashed_data] = k

    return dict(qualified_edges), dict(unqualified_edges)


def update_metadata(source, target):
    """Update the namespace and annotation metadata in the target graph.

    :param pybel.BELGraph source:
    :param pybel.BELGraph target:
    """
    target.namespace_url.update(source.namespace_url)
    target.namespace_pattern.update(source.namespace_pattern)
    target.annotation_url.update(source.annotation_url)
    target.annotation_pattern.update(source.annotation_pattern)
    target.annotation_list.update(source.annotation_list)


def update_node_helper(source, target):
    """Update the nodes' data dictionaries in the target graph from the source graph.

    :param nx.Graph source: The universe of all knowledge
    :param nx.Graph target: The target BEL graph
    """
    for node in target:
        if node not in source:
            continue
        target.node[node].update(source.node[node])


def ensure_node_from_universe(source, target, node):
    """Ensure the target graph has the given node using data from the source graph.

    :param pybel.BELGraph source: The universe of all knowledge
    :param pybel.BELGraph target: The target BEL graph
    :param tuple node: A BEL node
    """
    if node not in target:
        target.add_node(node, attr_dict=source.node[node])
