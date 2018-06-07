# -*- coding: utf-8 -*-

from ...pipeline import in_place_transformation
from ....constants import FUNCTION, MIRNA, NAMESPACE, PROTEIN, RNA, VARIANTS

__all__ = [
    'infer_central_dogmatic_translations_by_namespace',
    'infer_central_dogmatic_transcriptions',
    'infer_central_dogmatic_translations',
    'infer_central_dogma',
]


def _infer_converter_helper(node, data, new_function):
    new_tup = list(node)
    new_tup[0] = new_function
    new_tup = tuple(new_tup)
    new_dict = data.copy()
    new_dict[FUNCTION] = new_function
    return new_tup, new_dict


@in_place_transformation
def infer_central_dogmatic_translations_by_namespace(graph, namespaces):
    """Adds the missing origin :class:`pybel.dsl.rna` and RNA-Protein translation edge for all proteins.

    :param pybel.BELGraph graph: A BEL graph
    :param str or iter[str] namespaces: The namespaces over which to do this
    """
    namespaces = {namespaces} if isinstance(namespaces, str) else set(namespaces)

    for _, data in graph.nodes(data=True):
        if data[FUNCTION] != PROTEIN:
            continue

        if NAMESPACE not in data:
            continue

        if VARIANTS in data:
            continue

        if data[NAMESPACE] not in namespaces:
            continue

        graph.add_translation(data.get_rna(), data)


@in_place_transformation
def infer_central_dogmatic_translations(graph):
    """Add the missing origin RNA and RNA-Protein translation edge for all HGNC Protein entities.

    :param pybel.BELGraph graph: A BEL graph
    """
    infer_central_dogmatic_translations_by_namespace(graph, 'HGNC')


@in_place_transformation
def infer_central_dogmatic_transcriptions(graph):
    """Add the missing origin Gene and Gene-RNA transcription edge for all RNA entities.

    :param pybel.BELGraph graph: A BEL graph
    """
    for _, data in graph.nodes(data=True):
        if data[FUNCTION] not in {MIRNA, RNA}:
            continue

        if NAMESPACE not in data:
            continue

        if VARIANTS in data:
            continue

        graph.add_transcription(data.get_gene(), data)


@in_place_transformation
def infer_central_dogma(graph):
    """Add all RNA-Protein translations then all Gene-RNA transcriptions.

     Applies :func:`infer_central_dogmatic_translations` then :func:`infer_central_dogmatic_transcriptions` in
     succession.

    :param pybel.BELGraph graph: A BEL graph
    """
    infer_central_dogmatic_translations(graph)
    infer_central_dogmatic_transcriptions(graph)
