# -*- coding: utf-8 -*-

"""This module contains IO functions for outputting BEL graphs to lossy formats, such as GraphML and CSV"""

from __future__ import print_function

import json
import logging

import networkx as nx

from ..canonicalize import edge_to_bel
from ..constants import NAME, NAMESPACE
from ..struct import BELGraph
from ..utils import flatten_dict

__all__ = [
    'to_graphml',
    'to_csv',
    'to_sif',
    'to_gsea',
]

log = logging.getLogger(__name__)


def to_graphml(graph, file):
    """Writes this graph to GraphML XML file using :func:`networkx.write_graphml`. The .graphml file extension is
    suggested so Cytoscape can recognize it.

    :param BELGraph graph: A BEL graph
    :param file file: A file or file-like object
    """
    g = nx.MultiDiGraph()

    for node, data in graph.nodes(data=True):
        g.add_node(node, json=json.dumps(data))

    for u, v, key, data in graph.edges(data=True, keys=True):
        g.add_edge(u, v, key=key, attr_dict=flatten_dict(data))

    nx.write_graphml(g, file)


def to_csv(graph, file=None, sep='\t'):
    """Writes the graph as a tab-separated edge list with the columns:

    1. Source BEL term
    2. Relation
    3. Target BEL term
    4. Edge data dictionary.

    See the Data Models section of the documentation for which data are stored in the edge data dictionary, such
    as queryable information about transforms on the subject and object and their associated metadata.

    :param BELGraph graph: A BEL graph
    :param file file: A writable file or file-like. Defaults to stdout.
    :param str sep: The separator. Defaults to tab.
    """
    for u, v, data in graph.edges_iter(data=True):
        print(
            edge_to_bel(graph, u, v, data=data, sep=sep),
            json.dumps(data),
            sep=sep,
            file=file
        )


def to_sif(graph, file=None, sep='\t'):
    """Writes the graph as a tab-separated SIF file with the following columns:

    1. Source BEL term
    2. Relation
    3. Target BEL term

    This format is simple and can be used readily with many applications, but is lossy in that it does not include
    relation metadata.

    :param BELGraph graph: A BEL graph
    :param file file: A writable file or file-like. Defaults to stdout.
    :param str sep: The separator. Defaults to tab.
    """
    for u, v, data in graph.edges_iter(data=True):
        print(
            edge_to_bel(graph, u, v, data=data, sep=sep),
            file=file
        )


def to_gsea(graph, file=None):
    """Writes the genes/gene products to a GRP file for use with GSEA gene set enrichment analysis

    :param BELGraph graph: A BEL graph 
    :param file file: A writeable file or file-like object. Defaults to stdout.

    .. seealso::

        - GRP `format specification <http://software.broadinstitute.org/cancer/software/gsea/wiki/index.php/Data_formats#GRP:_Gene_set_file_format_.28.2A.grp.29>`_
        - GSEA `publication <https://doi.org/10.1073/pnas.0506580102>`_

    """
    print('# {}'.format(graph.name), file=file)
    nodes = {
        d[NAME]
        for _, d in graph.nodes_iter(data=True)
        if NAMESPACE in d and d[NAMESPACE] == 'HGNC'
    }
    for node in sorted(nodes):
        print(node, file=file)
