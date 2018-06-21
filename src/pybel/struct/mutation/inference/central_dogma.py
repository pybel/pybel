# -*- coding: utf-8 -*-

from ...pipeline import in_place_transformation
from ....constants import FUNCTION, IDENTIFIER, MIRNA, NAME, NAMESPACE, PROTEIN, RNA, VARIANTS
from ....dsl import gene, rna

__all__ = [
    'infer_central_dogmatic_transcriptions',
    'infer_central_dogmatic_translations',
    'infer_central_dogma',
]


@in_place_transformation
def infer_central_dogmatic_translations(graph):
    """Add the missing origin RNA and RNA-Protein translation edge for all Protein entities.

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


@in_place_transformation
def infer_central_dogmatic_transcriptions(graph):
    """Add the missing origin Gene and Gene-RNA transcription edge for all RNA entities.

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


@in_place_transformation
def infer_central_dogma(graph):
    """Add all RNA-Protein translations then all Gene-RNA transcriptions.

     Applies :func:`infer_central_dogmatic_translations` then :func:`infer_central_dogmatic_transcriptions` in
     succession.

    :param pybel.BELGraph graph: A BEL graph
    """
    infer_central_dogmatic_translations(graph)
    infer_central_dogmatic_transcriptions(graph)
