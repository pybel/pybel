# -*- coding: utf-8 -*-

"""This module facilitates the transfer of knowledge through ontological relationships."""

from typing import Iterable, List

from ...graph import BELGraph
from ....constants import (
    ANNOTATIONS, CAUSAL_RELATIONS, CITATION, EVIDENCE, IS_A, RELATION, SOURCE_MODIFIER,
    TARGET_MODIFIER,
)
from ....dsl import BaseEntity

__all__ = [
    'infer_child_relations',
]


def iter_children(graph: BELGraph, node: BaseEntity) -> Iterable[BaseEntity]:
    """Iterate over children of the node."""
    return (
        node
        for node, _, d in graph.in_edges(node, data=True)
        if d[RELATION] == IS_A
    )


def transfer_causal_edges(graph: BELGraph, source: BaseEntity, target: BaseEntity) -> Iterable[str]:
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
            source_modifier=data.get(SOURCE_MODIFIER),
            target_modifier=data.get(TARGET_MODIFIER),
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
            source_modifier=data.get(SOURCE_MODIFIER),
            target_modifier=data.get(TARGET_MODIFIER),
        )


def infer_child_relations(graph: BELGraph, node: BaseEntity) -> List[str]:
    """Propagate causal relations to children."""
    return list(_infer_child_relations_iter(graph, node))


def _infer_child_relations_iter(graph: BELGraph, node: BaseEntity) -> Iterable[str]:
    """Propagate causal relations to children."""
    for child in iter_children(graph, node):
        yield from transfer_causal_edges(graph, node, child)
        yield from infer_child_relations(graph, child)
