# -*- coding: utf-8 -*-

"""This module contains IO functions for outputting BEL graphs to lossy formats, such as GraphML and CSV."""

from __future__ import print_function

import json
import logging

import networkx as nx

from ..constants import FUNCTION, NAME, NAMESPACE, RELATION
from ..struct import BELGraph

__all__ = [
    'to_graphml',
    'to_csv',
    'to_sif',
    'to_gsea',
]

log = logging.getLogger(__name__)


def to_graphml(graph, file):
    """Write this graph to GraphML XML file using :func:`networkx.write_graphml`.

    The .graphml file extension is suggested so Cytoscape can recognize it.

    :param BELGraph graph: A BEL graph
    :param file file: A file or file-like object
    """
    graph = nx.MultiDiGraph()

    for node in graph:
        graph.add_node(node.as_bel(), function=node.function)

    for u, v, key, node in graph.edges(data=True, keys=True):
        graph.add_edge(
            u.as_bel(),
            v.as_bel(),
            key=key,
            interaction=node[RELATION],
        )

    nx.write_graphml(graph, file)


def to_csv(graph, file=None, sep='\t'):
    """Write the graph as a tab-separated edge list.

    The resulting file will contain the following columns:

    1. Source BEL term
    2. Relation
    3. Target BEL term
    4. Edge data dictionary

    See the Data Models section of the documentation for which data are stored in the edge data dictionary, such
    as queryable information about transforms on the subject and object and their associated metadata.

    :param BELGraph graph: A BEL graph
    :param file file: A writable file or file-like. Defaults to stdout.
    :param str sep: The separator. Defaults to tab.
    """
    for u, v, data in graph.edges(data=True):
        print(
            graph.edge_to_bel(u, v, data=data, sep=sep),
            json.dumps(data),
            sep=sep,
            file=file
        )


def to_sif(graph, file=None, sep='\t'):
    """Write the graph as a tab-separated SIF file.

    The resulting file will contain the following columns:

    1. Source BEL term
    2. Relation
    3. Target BEL term

    This format is simple and can be used readily with many applications, but is lossy in that it does not include
    relation metadata.

    :param BELGraph graph: A BEL graph
    :param file file: A writable file or file-like. Defaults to stdout.
    :param str sep: The separator. Defaults to tab.
    """
    for u, v, data in graph.edges(data=True):
        print(
            graph.edge_to_bel(u, v, data=data, sep=sep),
            file=file
        )


def to_gsea(graph, file=None):
    """Write the genes/gene products to a GRP file for use with GSEA gene set enrichment analysis.

    :param BELGraph graph: A BEL graph 
    :param file file: A writeable file or file-like object. Defaults to stdout.

    .. seealso::

        - GRP `format specification <http://software.broadinstitute.org/cancer/software/gsea/wiki/index.php/Data_formats#GRP:_Gene_set_file_format_.28.2A.grp.29>`_
        - GSEA `publication <https://doi.org/10.1073/pnas.0506580102>`_

    """
    print('# {}'.format(graph.name), file=file)
    nodes = {
        data[NAME]
        for data in graph
        if NAMESPACE in data and data[NAMESPACE] == 'HGNC' and NAME in data
    }
    for node in sorted(nodes):
        print(node, file=file)
