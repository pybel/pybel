# -*- coding: utf-8 -*-

"""This module facilitates the transfer of knowledge through ontological relationships."""

from ...constants import ANNOTATIONS, CAUSAL_RELATIONS, CITATION, EVIDENCE, IS_A, OBJECT, RELATION, SUBJECT
from ...dsl.nodes import BaseEntity

__all__ = [
    'infer_child_relations'
]


def iter_children(graph, node):
    """Iterate over children of the node.

    :param pybel.BELGraph graph:
    :param tuple node:
    :rtype: iter[tuple]
    """
    for u, _, d in graph.in_edges(node, data=True):
        if d[RELATION] != IS_A:
            continue
        yield u


def transfer_causal_edges(graph, source, target):
    """Transfer causal edges that the source has to the target.

    :param pybel.BELGraph graph:
    :param tuple source:
    :param tuple target:
    """
    for _, v, k, d in graph.out_edges(source, keys=True, data=True):
        if d[RELATION] not in CAUSAL_RELATIONS:
            continue

        graph.add_qualified_edge(
            target,
            v,
            relation=d[RELATION],
            evidence=d[EVIDENCE],
            citation=d[CITATION],
            annotations=d.get(ANNOTATIONS),
            subject_modifier=d.get(SUBJECT),
            object_modifier=d.get(OBJECT)
        )

    for u, _, k, d in graph.in_edges(source, keys=True, data=True):
        if d[RELATION] not in CAUSAL_RELATIONS:
            continue

        graph.add_qualified_edge(
            u,
            target,
            relation=d[RELATION],
            evidence=d[EVIDENCE],
            citation=d[CITATION],
            annotations=d.get(ANNOTATIONS),
            subject_modifier=d.get(SUBJECT),
            object_modifier=d.get(OBJECT)
        )


def infer_child_relations(graph, node):
    """Propagate causal relations to children.

    :param pybel.BELGraph graph: A BEL graph
    :param node: A PyBEL node tuple, on which to propagate the children's relations
    :type node: tuple or BaseEntity
    """
    if isinstance(node, BaseEntity):
        node = node.as_tuple()

    for child in iter_children(graph, node):
        transfer_causal_edges(graph, node, child)
        infer_child_relations(graph, child)
