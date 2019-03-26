# -*- coding: utf-8 -*-

"""This module contains IO functions for outputting BEL graphs to lossy formats, such as GraphML and CSV."""

import json
from typing import BinaryIO, Optional, TextIO, Union

import networkx as nx

from ..constants import NAME, NAMESPACE, RELATION
from ..struct import BELGraph

__all__ = [
    'to_graphml',
    'to_csv',
    'to_csv_path',
    'to_sif',
    'to_sif_path',
    'to_gsea',
    'to_gsea_path',
]


def to_graphml(graph: BELGraph, path: Union[str, BinaryIO]) -> None:
    """Write this graph to GraphML XML file using :func:`networkx.write_graphml`.

    The .graphml file extension is suggested so Cytoscape can recognize it.
    """
    rv = nx.MultiDiGraph()

    for node in graph:
        rv.add_node(node.as_bel(), function=node.function)

    for u, v, key, edge_data in graph.edges(data=True, keys=True):
        rv.add_edge(
            u.as_bel(),
            v.as_bel(),
            interaction=edge_data[RELATION],
            bel=graph.edge_to_bel(u, v, edge_data),
            key=key,
        )

    nx.write_graphml(rv, path)


def to_csv(graph: BELGraph, file: Optional[TextIO] = None, sep: Optional[str] = None) -> None:
    """Write the graph as a tab-separated edge list.

    The resulting file will contain the following columns:

    1. Source BEL term
    2. Relation
    3. Target BEL term
    4. Edge data dictionary

    See the Data Models section of the documentation for which data are stored in the edge data dictionary, such
    as queryable information about transforms on the subject and object and their associated metadata.
    """
    if sep is None:
        sep = '\t'

    for u, v, data in graph.edges(data=True):
        print(
            graph.edge_to_bel(u, v, edge_data=data, sep=sep),
            json.dumps(data),
            sep=sep,
            file=file,
        )


def to_csv_path(graph: BELGraph, path: str, sep: Optional[str] = None) -> None:
    """Write the graph as a tab-separated edge list to a file at the given path."""
    with open(path, 'w') as file:
        to_csv(graph, file, sep=sep)


def to_sif(graph: BELGraph, file: Optional[TextIO] = None, sep: Optional[str] = None) -> None:
    """Write the graph as a tab-separated SIF file.

    The resulting file will contain the following columns:

    1. Source BEL term
    2. Relation
    3. Target BEL term

    This format is simple and can be used readily with many applications, but is lossy in that it does not include
    relation metadata.
    """
    if sep is None:
        sep = '\t'

    for u, v, data in graph.edges(data=True):
        print(
            graph.edge_to_bel(u, v, edge_data=data, sep=sep),
            file=file,
        )


def to_sif_path(graph: BELGraph, path: str, sep: Optional[str] = None) -> None:
    """Write the graph as a tab-separated SIF file. to a file at the given path."""
    with open(path, 'w') as file:
        to_sif(graph, file, sep=sep)


def to_gsea(graph: BELGraph, file: Optional[TextIO] = None) -> None:
    """Write the genes/gene products to a GRP file for use with GSEA gene set enrichment analysis.

    .. seealso::

        - GRP `format specification <http://software.broadinstitute.org/cancer/software/gsea/wiki/index.php/Data_formats#GRP:_Gene_set_file_format_.28.2A.grp.29>`_
        - GSEA `publication <https://doi.org/10.1073/pnas.0506580102>`_
    """
    print('# {}'.format(graph.name), file=file)
    nodes = {
        data[NAME]
        for data in graph
        if NAMESPACE in data and data[NAMESPACE].upper() == 'HGNC' and NAME in data
    }
    for node in sorted(nodes):
        print(node, file=file)


def to_gsea_path(graph: BELGraph, path: str) -> None:
    """Write the genes/gene products to a GRP file at the given path for use with GSEA gene set enrichment analysis."""
    with open(path, 'w') as file:
        to_gsea(graph, file)
