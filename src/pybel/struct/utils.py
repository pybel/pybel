# -*- coding: utf-8 -*-

__all__ = [
    'update_metadata',
    'update_node_helper',
    'ensure_node_from_universe',
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
        target.add_node(node, **source.node[node])
