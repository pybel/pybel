# -*- coding: utf-8 -*-

from collections import defaultdict

from .collapse import collapse_nodes
from ..inference import enrich_protein_and_rna_origins
from ...pipeline.decorators import in_place_transformation, register_deprecated
from ....constants import RELATION, TRANSCRIBED_TO, TRANSLATED_TO

__all__ = [
    'collapse_to_genes',
]


def _build_collapse_to_gene_dict(graph):
    """
    :param pybel.BELGraph graph: A BEL graph
    :return: A dictionary of {node: set of PyBEL node tuples}
    :rtype: dict[tuple,set[tuple]]
    """
    collapse_dict = defaultdict(set)
    r2g = {}

    for gene_node, rna_node, d in graph.edges(data=True):
        if d[RELATION] != TRANSCRIBED_TO:
            continue

        collapse_dict[gene_node].add(rna_node)
        r2g[rna_node] = gene_node

    for rna_node, protein_node, d in graph.edges(data=True):
        if d[RELATION] != TRANSLATED_TO:
            continue

        if rna_node not in r2g:
            raise ValueError('Should complete origin before running this function')

        collapse_dict[r2g[rna_node]].add(protein_node)

    return collapse_dict


@register_deprecated('collapse_by_central_dogma')
@in_place_transformation
def collapse_to_genes(graph):
    """Collapse all protein, RNA, and miRNA nodes to their corresponding gene nodes.

    :param pybel.BELGraph graph: A BEL graph
    """
    enrich_protein_and_rna_origins(graph)
    collapse_dict = _build_collapse_to_gene_dict(graph)
    collapse_nodes(graph, collapse_dict)
