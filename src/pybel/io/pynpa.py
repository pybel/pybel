# -*- coding: utf-8 -*-

"""Exporter for PyNPA.

.. seealso:: https://github.com/pynpa
"""

import logging
import os
from typing import List, Mapping, Optional, Tuple

import pandas as pd

from ..constants import CAUSAL_DECREASE_RELATIONS, CAUSAL_INCREASE_RELATIONS, RELATION
from ..dsl import Gene, MicroRna, Protein, Rna
from ..struct import BELGraph
from ..struct.getters import get_tf_pairs
from ..struct.node_utils import list_abundance_cartesian_expansion, reaction_cartesian_expansion

__all__ = [
    'to_npa_directory',
    'to_npa_dfs',
    'to_npa_layers',
]

logger = logging.getLogger(__name__)

Layer = Mapping[Tuple[Gene, Gene], int]

#: Code to distinguish between between iNodes when nodes have been debelized
DEBELIZED_CODE_FOR_INODES = "*"


def to_npa_directory(graph: BELGraph, directory: str, **kwargs) -> None:
    """Write the BEL file to two files in the directory for :mod:`pynpa`."""
    ppi_df, transcription_df = to_npa_dfs(graph, **kwargs)
    ppi_df.to_csv(os.path.join(directory, 'ppi_layer.tsv'), sep='\t', index=False)
    transcription_df.to_csv(os.path.join(directory, 'transcriptional_layer.tsv'), sep='\t', index=False)


def to_npa_dfs(
    graph: BELGraph,
    cartesian_expansion: bool = False,
    nomenclature_method_first_layer: Optional[str] = None,
    nomenclature_method_second_layer: Optional[str] = None,
    direct_tf_only: bool = False,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Export the BEL graph as two lists of triples for the :mod:`pynpa`.

    :param graph: A BEL graph
    :param cartesian_expansion: If true, applies cartesian expansion on both reactions (reactants x products)
     as well as list abundances using :func:`list_abundance_cartesian_expansion` and
     :func:`reaction_cartesian_expansion`
    :param nomenclature_method_first_layer: Either "curie", "name" or "inodes. Defaults to "curie".
    :param nomenclature_method_second_layer: Either "curie", "name" or "inodes. Defaults to "curie".

    1. Pick out all transcription factor relationships. Protein X is a transcription
       factor for gene Y IFF ``complex(p(X), g(Y)) -> r(Y)``
    2. Get all other interactions between any gene/rna/protein that are directed causal
       for the PPI layer
    """
    ppi_layer, transcription_layer = to_npa_layers(
        graph,
        cartesian_expansion=cartesian_expansion,
        direct_tf_only=direct_tf_only,
    )
    return (
        _get_df(ppi_layer, method=nomenclature_method_first_layer),
        _get_df(transcription_layer, method=nomenclature_method_second_layer),
    )


def _get_df(layer: Layer, method: Optional[str] = None) -> pd.DataFrame:
    rows = _normalize_layer(layer, method=method)
    return pd.DataFrame(rows, columns=['source', 'target', 'relation']).sort_values(['source', 'target'])


def _normalize_layer(layer: Layer, method: Optional[str] = None) -> List[Tuple[str, str, int]]:
    if method == 'curie' or method is None:
        return [
            (source.curie, target.curie, direction)
            for (source, target), direction in layer.items()
        ]
    elif method == 'name':
        return [
            (source.name, target.name, direction)
            for (source, target), direction in layer.items()
        ]
    elif method == 'inodes':
        return [
            (
                "{}{}".format(DEBELIZED_CODE_FOR_INODES, source.name),
                "{}{}".format(DEBELIZED_CODE_FOR_INODES, target.name),
                direction,
            )
            for (source, target), direction in layer.items()
        ]
    else:
        raise ValueError('Invalid export method: {method}'.format(method=method))


def to_npa_layers(
    graph: BELGraph,
    cartesian_expansion: bool = False,
    direct_tf_only: bool = False,
) -> Tuple[Layer, Layer]:
    """Get the two layers for the network.

    :param graph: A BEL graph
    :param cartesian_expansion: If true, applies cartesian expansion on both reactions (reactants x products)
     as well as list abundances using :func:`list_abundance_cartesian_expansion` and
     :func:`reaction_cartesian_expansion`
    :param direct_tf_only: If true, only uses directlyIncreases and directlyDecreases relations for TF relations
     ``complex(p(X), g(Y)) =>/=| r(Y)``. If false, also allows indirect relations ``complex(p(X), g(Y)) ->/-| r(Y)``.
    """
    if cartesian_expansion:
        list_abundance_cartesian_expansion(graph)
        reaction_cartesian_expansion(graph)

    transcription_layer = {
        (u.get_rna().get_gene(), v.get_gene()): r
        for u, v, r in get_tf_pairs(graph, direct_only=direct_tf_only)
    }
    logger.info('extracted %d pairs for the transcription layer', len(transcription_layer))

    ppi_layer = {}
    for u, v, d in graph.edges(data=True):
        u, v = _normalize(u), _normalize(v)
        if u is None or v is None:
            continue
        if (u, v) in transcription_layer:
            continue
        relation = d[RELATION]

        if relation in CAUSAL_INCREASE_RELATIONS:
            ppi_layer[u, v] = +1
        elif relation in CAUSAL_DECREASE_RELATIONS:
            ppi_layer[u, v] = -1
        # TODO what about contradictions

    logger.info('extracted %d pairs for the ppi layer', len(ppi_layer))
    return ppi_layer, transcription_layer


def _normalize(n):
    if isinstance(n, Protein):
        if n.variants:
            n = n.get_parent()
        n = n.get_rna()
    if isinstance(n, (Rna, MicroRna)):
        if n.variants:
            n = n.get_parent()
        n = n.get_gene()
    if isinstance(n, Gene):
        if n.variants:
            n = n.get_parent()
        return n
