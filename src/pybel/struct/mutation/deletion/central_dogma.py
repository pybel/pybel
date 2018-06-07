# -*- coding: utf-8 -*-

from ...filters.node_selection import get_nodes_by_function
from ...pipeline import in_place_transformation
from ....constants import GENE, RELATION, RNA, TRANSCRIBED_TO, TRANSLATED_TO

__all__ = [
    'prune_central_dogma',
]


def get_gene_leaves(graph):
    """Iterate over all genes who have only one connection, that's a transcription to its RNA.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: iter[tuple]
    """
    for node in get_nodes_by_function(graph, GENE):
        if graph.in_degree(node) != 0:
            continue

        if graph.out_degree(node) != 1:
            continue

        _, _, d = graph.out_edges(node, data=True)[0]

        if d[RELATION] == TRANSCRIBED_TO:
            yield node


def get_rna_leaves(graph):
    """Iterate over all RNAs who have only one connection, that's a translation to its protein.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: iter[tuple]
    """
    for node in get_nodes_by_function(graph, RNA):
        if graph.in_degree(node) != 0:
            continue

        if graph.out_degree(node) != 1:
            continue

        _, _, d = graph.out_edges(node, data=True)[0]

        if d[RELATION] == TRANSLATED_TO:
            yield node


@in_place_transformation
def prune_central_dogma(graph):
    """Prune genes, then RNA, in place.

    :param pybel.BELGraph graph: A BEL graph
    """
    gene_leaves = list(get_gene_leaves(graph))
    graph.remove_nodes_from(gene_leaves)

    rna_leaves = list(get_rna_leaves(graph))
    graph.remove_nodes_from(rna_leaves)
