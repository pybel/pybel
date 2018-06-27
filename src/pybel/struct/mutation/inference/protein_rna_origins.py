# -*- coding: utf-8 -*-

from ...pipeline import in_place_transformation
from ...pipeline.decorators import register_deprecated
from ....constants import FUNCTION, IDENTIFIER, MIRNA, NAME, NAMESPACE, PROTEIN, RNA, VARIANTS
from ....dsl import gene, rna

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
    for protein_node, data in graph.nodes(data=True):
        if data[FUNCTION] != PROTEIN:
            continue

        namespace = data.get(NAMESPACE)
        if namespace is None:
            continue

        if VARIANTS in data:
            continue

        rna_node = rna(
            namespace=namespace,
            name=data.get(NAME),
            identifier=data.get(IDENTIFIER),
        )
        graph.add_translation(rna_node, protein_node)


@register_deprecated('infer_central_dogmatic_transcriptions')
@in_place_transformation
def enrich_rnas_with_genes(graph):
    """Add the corresponding gene node for each RNA/miRNA node and connect them with a transcription edge.

    :param pybel.BELGraph graph: A BEL graph
    """
    for rna_node, data in graph.nodes(data=True):
        if data[FUNCTION] not in {MIRNA, RNA}:
            continue

        namespace = data.get(NAMESPACE)
        if namespace is None:
            continue

        if VARIANTS in data:
            continue

        gene_node = gene(
            namespace=namespace,
            name=data.get(NAME),
            identifier=data.get(IDENTIFIER),
        )
        graph.add_transcription(gene_node, rna_node)


@register_deprecated('infer_central_dogma')
@in_place_transformation
def enrich_protein_and_rna_origins(graph):
    """Add the corresponding RNA for each protein then the corresponding gene for each RNA/miRNA.

    :param pybel.BELGraph graph: A BEL graph
    """
    enrich_proteins_with_rnas(graph)
    enrich_rnas_with_genes(graph)
