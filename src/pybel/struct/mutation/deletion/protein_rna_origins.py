# -*- coding: utf-8 -*-

"""Functions for deleting proteins and genes that are leaves."""

from typing import Iterable

from ...filters.node_selection import get_nodes_by_function
from ...pipeline.decorators import in_place_transformation, register_deprecated
from ....constants import GENE, RELATION, RNA, TRANSCRIBED_TO, TRANSLATED_TO
from ....dsl import BaseEntity

__all__ = [
    'prune_protein_rna_origins',
]


def get_gene_leaves(graph) -> Iterable[BaseEntity]:
    """Iterate over all genes who have only one connection, that's a transcription to its RNA.

    :param pybel.BELGraph graph: A BEL graph
    """
    for node in get_nodes_by_function(graph, GENE):
        if graph.in_degree(node) != 0:
            continue

        if graph.out_degree(node) != 1:
            continue

        _, _, d = list(graph.out_edges(node, data=True))[0]

        if d[RELATION] == TRANSCRIBED_TO:
            yield node


def get_rna_leaves(graph) -> Iterable[BaseEntity]:
    """Iterate over all RNAs who have only one connection, that's a translation to its protein.

    :param pybel.BELGraph graph: A BEL graph
    """
    for node in get_nodes_by_function(graph, RNA):
        if graph.in_degree(node) != 0:
            continue

        if graph.out_degree(node) != 1:
            continue

        _, _, d = list(graph.out_edges(node, data=True))[0]

        if d[RELATION] == TRANSLATED_TO:
            yield node


@in_place_transformation
def prune_rna_origins(graph):
    """Delete gene nodes that are only connected to one node, their correspond RNA, by a transcription edge.

    :param pybel.BELGraph graph: A BEL graph
    """
    gene_leaves = list(get_gene_leaves(graph))
    graph.remove_nodes_from(gene_leaves)


@in_place_transformation
def prune_protein_origins(graph):
    """Delete RNA nodes that are only connected to one node - their correspond protein - by a translation edge.

    :param pybel.BELGraph graph: A BEL graph
    """
    rna_leaves = list(get_rna_leaves(graph))
    graph.remove_nodes_from(rna_leaves)


@register_deprecated('prune_central_dogma')
@in_place_transformation
def prune_protein_rna_origins(graph):
    """Delete genes that are only connected to one node, their correspond RNA, by a translation edge.

    :param pybel.BELGraph graph: A BEL graph
    """
    prune_rna_origins(graph)
    prune_protein_origins(graph)
