# -*- coding: utf-8 -*-

"""This module contains IO functions for outputting BEL graphs to lossy formats, such as GraphML and CSV."""

import json
from typing import Optional, TextIO, Union

from networkx.utils import open_file

from ..dsl import CentralDogma
from ..struct import BELGraph

__all__ = [
    'to_csv',
    'to_sif',
    'to_gsea',
]


@open_file(1, mode='w')
def to_csv(graph: BELGraph, path: Union[str, TextIO], sep: Optional[str] = None) -> None:
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
            file=path,
        )


@open_file(1, mode='w')
def to_sif(graph: BELGraph, path: Union[str, TextIO], sep: Optional[str] = None) -> None:
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
            file=path,
        )


@open_file(1, mode='w')
def to_gsea(graph: BELGraph, path: Union[str, TextIO]) -> None:
    """Write the genes/gene products to a GRP file for use with GSEA gene set enrichment analysis.

    .. seealso::

        - GRP `format specification <http://software.broadinstitute.org/cancer/software/gsea/wiki/index.php/Data_formats#GRP:_Gene_set_file_format_.28.2A.grp.29>`_
        - GSEA `publication <https://doi.org/10.1073/pnas.0506580102>`_
    """
    print('# {}'.format(graph.name), file=path)
    hgnc_gene_symbols = {
        node.name
        for node in graph
        if isinstance(node, CentralDogma) and node.namespace.lower() == 'hgnc'
    }
    for hgnc_gene_symbol in sorted(hgnc_gene_symbols):
        print(hgnc_gene_symbol, file=path)
