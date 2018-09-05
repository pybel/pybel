# -*- coding: utf-8 -*-

import networkx as nx

__all__ = [
    'update_metadata',
    'update_node_helper',
    'ensure_node_from_universe',
    'relabel_inplace',
]


def update_metadata(source, target):
    """Update the namespace and annotation metadata in the target graph.

    :param pybel.BELGraph source:
    :param pybel.BELGraph target:
    """
    target.namespace_url.update(source.namespace_url)
    target.namespace_pattern.update(source.namespace_pattern)

    target.annotation_url.update(source.annotation_url)
    target.annotation_pattern.update(source.annotation_pattern)

    for keyword, values in source.annotation_list.items():
        if keyword not in target.annotation_list:
            target.annotation_list[keyword] = values
        else:
            for value in values:
                target.annotation_list[keyword].add(value)


def update_node_helper(source, target):
    """Update the nodes' data dictionaries in the target graph from the source graph.

    :param nx.Graph source: The universe of all knowledge
    :param nx.Graph target: The target BEL graph
    """
    for node in target:
        if node in source:
            target.nodes[node].update(source.nodes[node])


def ensure_node_from_universe(source, target, node):
    """Ensure the target graph has the given node using data from the source graph.

    :param pybel.BELGraph source: The universe of all knowledge
    :param pybel.BELGraph target: The target BEL graph
    :param tuple node: A BEL node
    """
    if node not in target:
        target.add_node(node)
        target._node[node] = source._node[node]


def relabel_inplace(G, mapping):  # borrowed from NX
    return nx.relabel_nodes(G, mapping, copy=False)
