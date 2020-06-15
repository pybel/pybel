# -*- coding: utf-8 -*-

"""Functions for enriching the origins of Proteins, RNAs, and miRNAs."""

from ...graph import BELGraph
from ...pipeline import in_place_transformation
from ....constants import FUNCTION, FUSION, MIRNA, RNA, VARIANTS
from ....dsl import Protein

__all__ = [
    'enrich_rnas_with_genes',
    'enrich_proteins_with_rnas',
    'enrich_protein_and_rna_origins',
]


@in_place_transformation
def enrich_proteins_with_rnas(graph: BELGraph) -> None:
    """Add the corresponding RNA node for each protein node and connect them with a translation edge.

    :param graph: A BEL graph
    """
    for protein_node in list(graph):
        if not isinstance(protein_node, Protein):
            continue

        if protein_node.variants:
            continue

        rna_node = protein_node.get_rna()
        graph.add_translation(rna_node, protein_node)


@in_place_transformation
def enrich_rnas_with_genes(graph: BELGraph) -> None:
    """Add the corresponding gene node for each RNA/miRNA node and connect them with a transcription edge.

    :param graph: A BEL graph
    """
    for rna_node in list(graph):
        if rna_node[FUNCTION] not in {MIRNA, RNA} or FUSION in rna_node or VARIANTS in rna_node:
            continue

        gene_node = rna_node.get_gene()
        graph.add_transcription(gene_node, rna_node)


@in_place_transformation
def enrich_protein_and_rna_origins(graph: BELGraph) -> None:
    """Add the corresponding RNA for each protein then the corresponding gene for each RNA/miRNA.

    :param graph: A BEL graph
    """
    enrich_proteins_with_rnas(graph)
    enrich_rnas_with_genes(graph)
