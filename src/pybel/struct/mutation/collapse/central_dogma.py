# -*- coding: utf-8 -*-

from collections import defaultdict

from .collapse import collapse_nodes
from ..inference import infer_central_dogma
from ...pipeline import in_place_transformation
from ....constants import RELATION, TRANSCRIBED_TO, TRANSLATED_TO

__all__ = [
    'build_central_dogma_collapse_dict',
    'collapse_by_central_dogma',
    'build_central_dogma_collapse_gene_dict',
    'collapse_by_central_dogma_to_genes',
]


def build_central_dogma_collapse_dict(graph):
    """Build a dictionary to direct the collapsing on the central dogma.

    :param pybel.BELGraph graph: A BEL graph
    :return: A dictionary of {node: set of nodes}
    :rtype: dict[tuple,set[tuple]]
    """
    collapse_dict = defaultdict(set)
    r2p = {}

    for rna_node, protein_node, d in graph.edges_iter(data=True):
        if d[RELATION] != TRANSLATED_TO:
            continue

        collapse_dict[protein_node].add(rna_node)
        r2p[rna_node] = protein_node

    for gene_node, rna_node, d in graph.edges_iter(data=True):
        if d[RELATION] != TRANSCRIBED_TO:
            continue

        if rna_node in r2p:
            collapse_dict[r2p[rna_node]].add(gene_node)
        else:
            collapse_dict[rna_node].add(gene_node)

    return collapse_dict


@in_place_transformation
def collapse_by_central_dogma(graph):
    """Collapses all nodes from the central dogma (GENE, RNA, PROTEIN) to PROTEIN, or most downstream possible entity,
    in place. This function wraps :func:`collapse_nodes` and :func:`build_central_dogma_collapse_dict`.

    :param pybel.BELGraph graph: A BEL graph

    Equivalent to:

    >>> collapse_nodes(graph, build_central_dogma_collapse_dict(graph))
    """
    collapse_dict = build_central_dogma_collapse_dict(graph)
    collapse_nodes(graph, collapse_dict)


def build_central_dogma_collapse_gene_dict(graph):
    """Build a dictionary to direct the collapsing on the central dogma.

    :param pybel.BELGraph graph: A BEL graph
    :return: A dictionary of {node: set of PyBEL node tuples}
    :rtype: dict[tuple,set[tuple]]
    """
    collapse_dict = defaultdict(set)
    r2g = {}

    for gene_node, rna_node, d in graph.edges_iter(data=True):
        if d[RELATION] != TRANSCRIBED_TO:
            continue

        collapse_dict[gene_node].add(rna_node)
        r2g[rna_node] = gene_node

    for rna_node, protein_node, d in graph.edges_iter(data=True):
        if d[RELATION] != TRANSLATED_TO:
            continue

        if rna_node not in r2g:
            raise ValueError('Should complete origin before running this function')

        collapse_dict[r2g[rna_node]].add(protein_node)

    return collapse_dict


@in_place_transformation
def collapse_by_central_dogma_to_genes(graph):
    """Collapses all nodes from the central dogma (:data:`pybel.constants.GENE`, :data:`pybel.constants.RNA`,
    :data:`pybel.constants.MIRNA`, and :data:`pybel.constants.PROTEIN`) to :data:`pybel.constants.GENE`, in-place. This
    function wraps :func:`collapse_nodes` and :func:`build_central_dogma_collapse_gene_dict`.

    :param pybel.BELGraph graph: A BEL graph

    Equivalent to:

    >>> infer_central_dogma(graph)
    >>> collapse_nodes(graph, build_central_dogma_collapse_gene_dict(graph))
    """
    infer_central_dogma(graph)
    collapse_dict = build_central_dogma_collapse_gene_dict(graph)
    collapse_nodes(graph, collapse_dict)
