# -*- coding: utf-8 -*-

"""Misc. getters."""

from typing import Iterable, Tuple

from .graph import BELGraph
from ..constants import (
    CAUSAL_DECREASE_RELATIONS, CAUSAL_INCREASE_RELATIONS, DIRECTLY_DECREASES, DIRECTLY_INCREASES,
    RELATION,
)
from ..dsl import ComplexAbundance, Gene, Protein, Rna

__all__ = [
    'get_tf_pairs',
]


def get_tf_pairs(graph: BELGraph, direct_only: bool = False) -> Iterable[Tuple[Protein, Rna, int]]:
    """Iterate pairs of ``p(X)`` and ``r(Y)`` such that ``complex(p(X), g(Y)) -> r(Y)``.

    :param graph: A BEL graph
    :param direct_only: If true, only uses directlyIncreases and directlyDecreases relations. Otherwise, allows
     indirect relations.
    """
    if direct_only:
        _inc, _dec = {DIRECTLY_INCREASES}, {DIRECTLY_DECREASES}
    else:
        _inc, _dec = CAUSAL_INCREASE_RELATIONS, CAUSAL_DECREASE_RELATIONS

    for tf in _iterate_proteins(graph):
        for tf_gene in graph[tf]:
            if not isinstance(tf_gene, ComplexAbundance):
                continue
            if tf not in tf_gene.members:
                continue
            other_members = [m for m in tf_gene.members if m != tf]
            if 1 != len(other_members):
                continue
            target_gene = other_members[0]
            if not isinstance(target_gene, Gene):
                continue
            if target_gene.variants:
                target_gene = target_gene.get_parent()
            target_rna = target_gene.get_rna()
            if target_rna not in graph:
                continue
            for edge in graph[tf_gene][target_rna].values():
                relation = edge[RELATION]
                if relation in _inc:
                    yield tf, target_rna, +1
                elif relation in _dec:
                    yield tf, target_rna, -1


def _iterate_proteins(graph: BELGraph) -> Iterable[Protein]:
    return (
        node
        for node in graph
        if isinstance(node, Protein)
    )
