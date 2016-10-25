import json
import logging
import os
import sys
import time

import networkx as nx
import py2neo
import requests
from networkx.readwrite import json_graph
from pybel.exceptions import PyBelWarning
from pybel.utils import flatten
from pyparsing import ParseException
from requests_file import FileAdapter

from .exceptions import PyBelError
from .manager.namespace_cache import DefinitionCacheManager
from .parser.parse_bel import BelParser
from .parser.parse_metadata import MetadataParser
from .parser.utils import split_file_to_annotations_and_definitions
from .utils import flatten_edges, expand_edges

__all__ = ['BELGraph', 'from_url', 'from_path', 'from_pickle',
           'from_graphml', 'to_graphml', 'to_json', 'to_neo4j', 'to_pickle']

log = logging.getLogger('pybel')

PYBEL_CONTEXT_TAG = 'pybel_context'


def from_url(url, **kwargs):
    """Loads a BEL graph from a URL resource

    :param url: a valid URL pointing to a BEL resource
    :type url: str
    :return: a parsed BEL graph
    :rtype: BELGraph
    """
    log.info('Loading from url: {}'.format(url))

    session = requests.session()
    if url.startswith('file://'):
        session.mount('file://', FileAdapter())
    response = session.get(url)
    response.raise_for_status()

    lines = (line.decode('utf-8') for line in response.iter_lines())

    return BELGraph(lines, **kwargs)


def from_path(path, **kwargs):
    """Loads a BEL graph from a file resource

    :param path: a file path
    :type path: str
    :return: a parsed BEL graph
    :rtype: BELGraph"""

    log.info('Loading from path: {}'.format(path))
    with open(os.path.expanduser(path)) as f:
        return BELGraph(f, **kwargs)


def from_database(connection):
    """Loads a BEL graph from a database

    :param connection: The string form of the URL is dialect[+driver]://user:password@host/dbname[?key=value..], where dialect is a database name such as mysql, oracle, postgresql, etc., and driver the name of a DBAPI, such as psycopg2, pyodbc, cx_oracle, etc. Alternatively, the URL can be an instance of URL.
    :type connection: str
    :return: a BEL graph loaded from the database
    :rtype: BELGraph
    """
    raise NotImplementedError("Can't load from from database: {}".format(connection))


class BELGraph(nx.MultiDiGraph):
    """An extension of a NetworkX MultiDiGraph to hold a BEL graph."""

    def __init__(self, lines, context=None, lenient=False, definition_cache_manager=None, *attrs, **kwargs):
        """Parses a BEL file from an iterable of strings. This can be a file, file-like, or list of strings.

        :param lines: iterable over lines of BEL data file
        :param context: disease context string
        :type context: str
        :param lenient: if true, allow naked namespaces
        :type lenient: bool
        :param definition_cache_manager: database connection string to namespace namspace_cache, pre-built namespace namspace_cache manager,
                    or True to use the default
        :type definition_cache_manager: str or pybel.mangager.NamespaceCache or bool
        """
        nx.MultiDiGraph.__init__(self, *attrs, **kwargs)

        self.context = context

        docs, defs, states = split_file_to_annotations_and_definitions(lines)

        if isinstance(definition_cache_manager, DefinitionCacheManager):
            self.metadata_parser = MetadataParser(definition_cache_manager=definition_cache_manager)
        elif isinstance(definition_cache_manager, str):
            self.metadata_parser = MetadataParser(definition_cache_manager=DefinitionCacheManager(conn=definition_cache_manager))
        else:
            self.metadata_parser = MetadataParser(definition_cache_manager=DefinitionCacheManager())

        self.parse_document(docs)

        self.parse_definitions(defs)

        self.bel_parser = BelParser(graph=self,
                                    valid_namespaces=self.metadata_parser.namespace_dict,
                                    valid_annotations=self.metadata_parser.annotations_dict,
                                    lenient=lenient)

        self.parse_statements(states)

    def clear(self):
        """Clears the content of the graph and its BEL parser"""
        self.bel_parser.clear()

    def parse_document(self, document_metadata):
        t = time.time()

        for line_number, line in document_metadata:
            try:
                self.metadata_parser.parseString(line)
            except:
                log.error('Line {:07} - failed: {}'.format(line_number, line))

        log.info('Finished parsing document section in {:.02f} seconds'.format(time.time() - t))

    def parse_definitions(self, definitions):
        t = time.time()

        for line_number, line in definitions:
            try:
                self.metadata_parser.parseString(line)
            except PyBelError as e:
                log.critical('Line {:07} - {}'.format(line_number, line))
                raise e
            except ParseException as e:
                log.error('Line {:07} - invalid statement: {}'.format(line_number, line))
            except PyBelWarning as e:
                log.warning('Line {:07} - {}: {}'.format(line_number, e, line))
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                log.error('Line {:07} - general failure: {} - {}: {}'.format(line_number, line, exc_type, exc_value))
                log.debug('Traceback: {}'.format(exc_traceback))

        log.info('Finished parsing definitions section in {:.02f} seconds'.format(time.time() - t))

    def parse_statements(self, statements):
        t = time.time()

        log.info('Streamlining BEL parser')
        self.bel_parser.language.streamline()
        log.info('Finished Streamlining BEL parser in {:.02f}s'.format(time.time() - t))

        t = time.time()

        for line_number, line in statements:
            try:
                self.bel_parser.parseString(line)
            except PyBelError as e:
                log.critical('Line {:07} - {}'.format(line_number, line))
                raise e
            except ParseException as e:
                log.error('Line {:07} - general parser failure: {}'.format(line_number, line))
            except PyBelWarning as e:
                log.debug('Line {:07} - {}'.format(line_number, e, line))
            except:
                log.error('Line {:07} - general failure: {}'.format(line_number, line))

        log.info('Finished parsing statements section in {:.02f} seconds'.format(time.time() - t))


def to_neo4j(graph, neo_graph, context=None):
    """Uploads a BEL graph to Neo4J graph database using `py2neo`

    :param graph: a BEL Graph
    :type graph: BELGraph
    :param neo_graph:
    :type neo_graph: py2neo.Graph
    :param context: a disease context to allow for multiple disease models in one neo4j instance
    :type context: str
    """

    if context is not None:
        graph.context = context

    tx = neo_graph.begin()

    node_map = {}
    for i, (node, data) in enumerate(graph.nodes(data=True)):
        node_type = data['type']
        attrs = {k: v for k, v in data.items() if k != 'type'}

        if 'name' in data:
            attrs['value'] = data['name']

        node_map[node] = py2neo.Node(node_type, cname=str(node), cnum=str(i), **attrs)

        tx.create(node_map[node])

    for u, v, data in graph.edges(data=True):
        neo_u = node_map[u]
        neo_v = node_map[v]
        rel_type = data['relation']
        attrs = flatten(data)
        if graph.context is not None:
            attrs[PYBEL_CONTEXT_TAG] = str(graph.context)
        rel = py2neo.Relationship(neo_u, rel_type, neo_v, **attrs)
        tx.create(rel)

    tx.commit()


def to_pickle(graph, output):
    """Writes this graph to a pickle object with nx.write_gpickle

    :param graph: a BEL graph
    :type graph: BELGraph
    :param output: a file or filename to write to
    """
    nx.write_gpickle(flatten_edges(graph), output)


def from_pickle(path):
    """Reads a graph from a gpickle file

    :param path: File or filename to write. Filenames ending in .gz or .bz2 will be uncompressed.
    :type path: file or list
    :rtype: nx.MultiDiGraph
    """
    return expand_edges(nx.read_gpickle(path))


def to_json(graph, output):
    """Writes this graph to a node-link JSON object

    :param graph: a BEL graph
    :type graph: BELGraph
    :param output: a write-supporting filelike object
    """
    data = json_graph.node_link_data(flatten_edges(graph))
    json.dump(data, output, ensure_ascii=False)


def to_graphml(graph, output):
    """Writes this graph to GraphML file. Use .graphml extension so Cytoscape can recognize it

    :param graph: a BEL graph
    :type graph: BELGraph
    :param output: a file or filelike object
    """
    nx.write_graphml(flatten_edges(graph), output)


def from_graphml(path):
    """Reads a graph from a graphml file

    :param path: File or filename to write. Filenames ending in .gz or .bz2 will be compressed.
    :type path: file or string
    :rtype: nx.MultiDiGraph
    """
    return expand_edges(nx.read_graphml(path))


def to_csv(graph, output):
    """Writes graph to edge list csv

    :param graph: a BEL graph
    :type graph: BELGraph
    :param output: a file or filelike object
    """
    nx.write_edgelist(flatten_edges(graph), output, data=True)
