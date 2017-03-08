# -*- coding: utf-8 -*-

"""

PyBEL provides functions for input and output to several formats. This includes:

- BEL Script (*.bel)
- Pickle object (*.pickle)
- GraphML (*.graphml)
- JSON (*.json)
- Edge list (*.csv)
- Relational database
- Neo4J graph database

It also includes utilities to handle bytes, line iterators, and fetching data from URL.

"""

import codecs
import json
import logging
import os

import networkx as nx
import py2neo
import requests
from networkx.readwrite.json_graph import node_link_data, node_link_graph
from pkg_resources import get_distribution
from requests_file import FileAdapter

from .canonicalize import decanonicalize_node
from .constants import PYBEL_CONTEXT_TAG, FUNCTION, NAME, RELATION, GRAPH_ANNOTATION_LIST
from .graph import BELGraph
from .utils import flatten_dict, flatten_graph_data, list2tuple

try:
    import cPickle as pickle
except ImportError:
    import pickle

__all__ = [
    'from_lines',
    'from_path',
    'from_url',
    'to_pickle',
    'to_bytes',
    'from_bytes',
    'from_pickle',
    'to_json',
    'from_json',
    'to_graphml',
    'to_csv',
    'to_neo4j'
]

log = logging.getLogger('pybel')


def tokenize_version(version_string):
    return tuple(version_string.split('.')[0:3])


def ensure_version(graph, check_version=True):
    """Ensure that the graph was produced on this version of python (disregard dev tags)

    TODO: in the future, just check that the minor versions are the same,
    because development won't be changing the data structure so much
    """
    current_version = tokenize_version(get_distribution('pybel').version)
    graph_version = tokenize_version(graph.pybel_version)
    if check_version and current_version != graph_version:
        raise ValueError('Using version {}, tried importing from version {}'.format(current_version, graph_version))
    return graph


def from_lines(lines, **kwargs):
    """Loads a BEL graph from an iterable over the lines of a BEL script. This can be a list of strings, file, or other.
    This function is a *very* thin wrapper around :class:`BELGraph`.

    :param lines: An iterable of strings (the lines in a BEL script)
    :type lines: iter
    :param kwargs: Keyword arguments to pass to :class:`pybel.BELGraph`
    :return: a parsed BEL graph
    :rtype: BELGraph
    """
    return BELGraph(lines=lines, **kwargs)


def from_path(path, encoding='utf-8', **kwargs):
    """Loads a BEL graph from a file resource

    :param path: A file path
    :type path: str
    :param encoding: the encoding to use when reading this file. Is passed to :code:`codecs.open`.
                     See the python `docs <https://docs.python.org/3/library/codecs.html#standard-encodings>`_ for a
                     list of standard encodings. For example, files starting with a UTF-8 BOM should use
                     :code:`utf_8_sig`
    :type encoding: str
    :param kwargs: Keyword arguments to pass to :class`pybel.BELGraph`
    :return: a parsed BEL graph
    :rtype: BELGraph
    """
    log.info('Loading from path: %s', path)
    with codecs.open(os.path.expanduser(path), encoding=encoding) as f:
        return BELGraph(lines=f, **kwargs)


def from_url(url, **kwargs):
    """Loads a BEL graph from a URL resource

    :param url: A valid URL pointing to a BEL resource
    :type url: str
    :param kwargs: Keyword arguments to pass to :class:`pybel.BELGraph`
    :return: a parsed BEL graph
    :rtype: BELGraph
    """
    log.info('Loading from url: %s', url)

    session = requests.session()
    session.mount('file://', FileAdapter())

    response = session.get(url)
    response.raise_for_status()

    lines = (line.decode('utf-8') for line in response.iter_lines())

    return BELGraph(lines=lines, **kwargs)


def to_bytes(graph, protocol=None):
    """Converts a graph to bytes with pickle

    :param graph: A BEL graph
    :type graph: BELGraph
    :param protocol: Pickling protocol to use
    :type protocol: int
    :rtype: bytes
    """
    if protocol is not None:
        return pickle.dumps(graph, protocol=protocol)
    else:
        return pickle.dumps(graph)


def from_bytes(bytes_graph, check_version=True):
    """Reads a graph from bytes (the result of pickling the graph)

    :param bytes_graph: File or filename to write
    :type bytes_graph: bytes
    :param check_version: Checks if the graph was produced by this version of PyBEL
    :type check_version: bool
    :rtype: BELGraph
    """
    return ensure_version(pickle.loads(bytes_graph), check_version)


def to_pickle(graph, output, protocol=None):
    """Writes this graph to a pickle object with nx.write_gpickle

    :param graph: A BEL graph
    :type graph: BELGraph
    :param output: A file or filename to write to
    :type output: file or file-like or str
    :param protocol: Pickling protocol to use
    :type protocol: int
    """
    if protocol is not None:
        nx.write_gpickle(graph, output, protocol=protocol)
    else:
        nx.write_gpickle(graph, output)


def from_pickle(path, check_version=True):
    """Reads a graph from a gpickle file

    :param path: File or filename to read. Filenames ending in .gz or .bz2 will be uncompressed.
    :type path: file or str
    :param check_version: Checks if the graph was produced by this version of PyBEL
    :type check_version: bool
    :rtype: BELGraph
    """
    return ensure_version(nx.read_gpickle(path), check_version=check_version)


def to_json_dict(graph):
    """Converts this graph to a node-link JSON object

    :param graph: A BEL graph
    :type graph: BELGraph
    :return: A node-link JSON object representing the given graph
    :rtype: dict
    """
    data = node_link_data(graph)
    data['graph'][GRAPH_ANNOTATION_LIST] = {k: list(sorted(v)) for k, v in
                                            data['graph'].get(GRAPH_ANNOTATION_LIST, {}).items()}
    return data


def to_jsons(graph):
    """Dumps this graph as a node-link JSON object to a string

    :param graph: A BEL graph
    :type graph: BELGraph
    :return: A string representation of the node-link JSON produced for this graph by :func:`to_json_dict`
    :rtype: str
    """
    return json.dumps(to_json_dict(graph), ensure_ascii=False)


def to_json(graph, output):
    """Writes this graph as a node-link JSON object

    :param graph: A BEL graph
    :type graph: BELGraph
    :param output: A write-supporting file or file-like object
    :type output: file
    """
    json_dict = to_json_dict(graph)
    json.dump(json_dict, output, ensure_ascii=False)


def from_json_dict(data, check_version=True):
    """Reads graph from node-link JSON Object

    :param data: A JSON dictionary representing a graph
    :type data: dict
    :param check_version: Checks if the graph was produced by this version of PyBEL
    :type check_version: bool
    :rtype: BELGraph
    """

    for i, node in enumerate(data['nodes']):
        data['nodes'][i]['id'] = list2tuple(data['nodes'][i]['id'])

    graph = node_link_graph(data, directed=True, multigraph=True)
    graph = BELGraph(data=graph)
    return ensure_version(graph, check_version=check_version)


def from_json(path, check_version=True):
    """Reads graph from node-link JSON Object

    :param path: file path to read
    :type path: str
    :param check_version: Checks if the graph was produced by this version of PyBEL
    :type check_version: bool
    :rtype: BELGraph
    """
    with open(os.path.expanduser(path)) as f:
        json_dict = json.load(f)
        graph = from_json_dict(json_dict, check_version=check_version)
        return graph


def to_graphml(graph, output):
    """Writes this graph to GraphML file. Use .graphml extension so Cytoscape can recognize it

    :param graph: A BEL graph
    :type graph: BELGraph
    :param output: A file or filelike object
    :type output: file
    """
    g = nx.MultiDiGraph()

    for node, data in graph.nodes(data=True):
        g.add_node(node, json=json.dumps(data))

    for u, v, key, data in graph.edges(data=True, keys=True):
        g.add_edge(u, v, key=key, attr_dict=flatten_dict(data))

    nx.write_graphml(g, output)


def to_csv(graph, output):
    """Writes graph to edge list csv

    :param graph: A BEL graph
    :type graph: BELGraph
    :param output: A file or filelike object
    :type output: file
    """
    nx.write_edgelist(flatten_graph_data(graph), output, data=True)


def to_neo4j(graph, neo_graph, context=None):
    """Uploads a BEL graph to Neo4J graph database using `py2neo`

    :param graph: A BEL Graph
    :type graph: BELGraph
    :param neo_graph: A py2neo graph object, Refer to the
                        `py2neo documentation <http://py2neo.org/v3/database.html#the-graph>`_
                        for how to build this object.
    :type neo_graph: :class:`py2neo.Graph`
    :param context: A disease context to allow for multiple disease models in one neo4j instance.
                    Each edge will be assigned an attribute :code:`pybel_context` with this value
    :type context: str
    """
    tx = neo_graph.begin()

    node_map = {}
    for node, data in graph.nodes(data=True):
        node_type = data[FUNCTION]
        attrs = {k: v for k, v in data.items() if k != FUNCTION}

        if NAME in data:
            attrs['value'] = data[NAME]

        node_map[node] = py2neo.Node(node_type, bel=decanonicalize_node(graph, node), **attrs)

        tx.create(node_map[node])

    for u, v, data in graph.edges(data=True):
        neo_u = node_map[u]
        neo_v = node_map[v]
        rel_type = data[RELATION]
        attrs = flatten_dict(data)
        if context is not None:
            attrs[PYBEL_CONTEXT_TAG] = str(context)
        rel = py2neo.Relationship(neo_u, rel_type, neo_v, **attrs)
        tx.create(rel)

    tx.commit()
