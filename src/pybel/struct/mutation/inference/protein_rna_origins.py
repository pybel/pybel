# -*- coding: utf-8 -*-

"""Functions for enriching the origins of Proteins, RNAs, and miRNAs."""

from pybel.dsl import Protein
from ...pipeline import in_place_transformation
from ...pipeline.decorators import register_deprecated
from ....constants import FUNCTION, FUSION, MIRNA, RNA, VARIANTS

__all__ = [
    'enrich_rnas_with_genes',
    'enrich_proteins_with_rnas',
    'enrich_protein_and_rna_origins',
]


@register_deprecated('infer_central_dogmatic_translations')
@in_place_transformation
def enrich_proteins_with_rnas(graph):
    """Add the corresponding RNA node for each protein node and connect them with a translation edge.

    :param pybel.BELGraph graph: A BEL graph
    """
    for protein_node in list(graph):
        if not isinstance(protein_node, Protein):
            continue

        if protein_node.variants:
            continue

        rna_node = protein_node.get_rna()
        graph.add_translation(rna_node, protein_node)


@register_deprecated('infer_central_dogmatic_transcriptions')
@in_place_transformation
def enrich_rnas_with_genes(graph):
    """Add the corresponding gene node for each RNA/miRNA node and connect them with a transcription edge.

    :param pybel.BELGraph graph: A BEL graph
    """
    for rna_node in list(graph):
        if rna_node[FUNCTION] not in {MIRNA, RNA} or FUSION in rna_node or VARIANTS in rna_node:
            continue

        gene_node = rna_node.get_gene()
        graph.add_transcription(gene_node, rna_node)


@register_deprecated('infer_central_dogma')
@in_place_transformation
def enrich_protein_and_rna_origins(graph):
    """Add the corresponding RNA for each protein then the corresponding gene for each RNA/miRNA.

    :param pybel.BELGraph graph: A BEL graph
    """
    enrich_proteins_with_rnas(graph)
    enrich_rnas_with_genes(graph)
