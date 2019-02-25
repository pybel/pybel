# -*- coding: utf-8 -*-

"""This module facilitates the transfer of knowledge through ontological relationships."""

from typing import Iterable, List

from ...constants import ANNOTATIONS, CAUSAL_RELATIONS, CITATION, EVIDENCE, IS_A, OBJECT, RELATION, SUBJECT
from ...dsl import BaseEntity

__all__ = [
    'infer_child_relations',
]


def iter_children(graph, node: BaseEntity) -> Iterable[BaseEntity]:
    """Iterate over children of the node."""
    return (
        node
        for node, _, d in graph.in_edges(node, data=True)
        if d[RELATION] == IS_A
    )


def transfer_causal_edges(graph, source: BaseEntity, target: BaseEntity) -> Iterable[str]:
    """Transfer causal edges that the source has to the target and yield the resulting hashes."""
    for _, v, data in graph.out_edges(source, data=True):
        if data[RELATION] not in CAUSAL_RELATIONS:
            continue

        yield graph.add_qualified_edge(
            target,
            v,
            relation=data[RELATION],
            evidence=data[EVIDENCE],
            citation=data[CITATION],
            annotations=data.get(ANNOTATIONS),
            subject_modifier=data.get(SUBJECT),
            object_modifier=data.get(OBJECT),
        )

    for u, _, data in graph.in_edges(source, data=True):
        if data[RELATION] not in CAUSAL_RELATIONS:
            continue

        yield graph.add_qualified_edge(
            u,
            target,
            relation=data[RELATION],
            evidence=data[EVIDENCE],
            citation=data[CITATION],
            annotations=data.get(ANNOTATIONS),
            subject_modifier=data.get(SUBJECT),
            object_modifier=data.get(OBJECT),
        )


def infer_child_relations(graph, node: BaseEntity) -> List[str]:
    """Propagate causal relations to children."""
    return list(_infer_child_relations_iter(graph, node))


def _infer_child_relations_iter(graph, node: BaseEntity) -> Iterable[str]:
    """Propagate causal relations to children."""
    for child in iter_children(graph, node):
        yield from transfer_causal_edges(graph, node, child)
        yield from infer_child_relations(graph, child)
