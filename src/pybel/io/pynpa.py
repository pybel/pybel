# -*- coding: utf-8 -*-

"""Exporter for PyNPA."""

import os
from typing import List, Mapping, Tuple

import pandas as pd

from ..constants import CAUSAL_DECREASE_RELATIONS, CAUSAL_INCREASE_RELATIONS, RELATION
from ..dsl import Gene, MicroRna, Protein, Rna
from ..struct import BELGraph
from ..struct.getters import get_tf_pairs

__all__ = [
    'to_npa_directory',
    'get_npa_layer_dfs',
    'get_npa_layers',
]

Layer = Mapping[Tuple[Gene, Gene], int]


def to_npa_directory(graph: BELGraph, directory: str) -> None:
    """Write the BEL file to two files in the directory for :mod:`pynpa`."""
    ppi_df, transcription_df = get_npa_layer_dfs(graph)
    ppi_df.to_csv(os.path.join(directory, 'ppi_layer.tsv'), sep='\t', index=False)
    transcription_df.to_csv(os.path.join(directory, 'transcriptional_layer.tsv'), sep='\t', index=False)


def get_npa_layer_dfs(graph: BELGraph) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Export the BEL graph as two lists of triples for the :mod:`pynpa`.

    1. Pick out all transcription factor relationships. Protein X is a transcription
       factor for gene Y IFF ``complex(p(X), g(Y)) -> r(Y)``
    2. Get all other interactions between any gene/rna/protein that are directed causal
       for the PPI layer
    """
    ppi_layer, transcription_layer = get_npa_layers(graph)
    return _get_df(ppi_layer), _get_df(transcription_layer)


def _get_df(layer: Layer) -> pd.DataFrame:
    rows = _normalize_layer(layer)
    return pd.DataFrame(rows, columns=['source', 'target', 'relation']).sort_values(['source', 'target'])


def _normalize_layer(layer: Layer) -> List[Tuple[str, str, int]]:
    return [
        (source.curie, target.curie, direction)
        for (source, target), direction in layer.items()
    ]


def get_npa_layers(graph: BELGraph) -> Tuple[Layer, Layer]:
    """Get the two layers for the network."""
    transcription_layer = {
        (u.get_rna().get_gene(), v.get_gene()): r
        for u, v, r in get_tf_pairs(graph)
    }

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
