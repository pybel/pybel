import json
import logging
import os
import sys
import time
from collections import defaultdict

import networkx as nx
import py2neo
import requests
from networkx.readwrite import GraphMLReader
from networkx.readwrite import json_graph
from pyparsing import ParseException
from requests_file import FileAdapter

from .exceptions import PyBelWarning
from .manager.cache import CacheManager
from .parser.canonicalize import decanonicalize_node, to_bel
from .parser.parse_bel import BelParser
from .parser.parse_metadata import MetadataParser
from .parser.utils import split_file_to_annotations_and_definitions, subdict_matches
from .utils import flatten, flatten_graph_data, expand_dict

__all__ = ['BELGraph', 'from_url', 'from_path', 'from_pickle', 'from_graphml', 'to_graphml', 'to_json', 'to_neo4j',
           'to_pickle', 'from_json', 'to_bel']

log = logging.getLogger('pybel')

PYBEL_CONTEXT_TAG = 'pybel_context'


def from_url(url, **kwargs):
    """Loads a BEL graph from a URL resource

    :param url: a valid URL pointing to a BEL resource
    :type url: str
    :param kwargs: keyword arguments to pass to :py:meth:`BELGraph`
    :return: a parsed BEL graph
    :rtype: BELGraph
    """
    log.info('Loading from url: %s', url)

    session = requests.session()
    if url.startswith('file://'):
        session.mount('file://', FileAdapter())
    response = session.get(url)
    response.raise_for_status()

    lines = (line.decode('utf-8') for line in response.iter_lines())

    return BELGraph(lines=lines, **kwargs)


def from_path(path, **kwargs):
    """Loads a BEL graph from a file resource

    :param path: a file path
    :type path: str
    :param kwargs: keyword arguments to pass to :py:meth:`BELGraph`
    :return: a parsed BEL graph
    :rtype: BELGraph"""

    log.info('Loading from path: %s', path)
    with open(os.path.expanduser(path)) as f:
        return BELGraph(lines=f, **kwargs)


def from_database(connection):
    """Loads a BEL graph from a database

    :param connection: The string form of the URL is :code:`dialect[+driver]://user:password@host/dbname[?key=value..]`,
                       where dialect is a database name such as mysql, oracle, postgresql, etc., and driver the name
                       of a DBAPI, such as psycopg2, pyodbc, cx_oracle, etc. Alternatively, the URL can be an instance
                       of URL.
    :type connection: str
    :return: a BEL graph loaded from the database
    :rtype: BELGraph
    """
    raise NotImplementedError("Can't load from from database: {}".format(connection))


class BELGraph(nx.MultiDiGraph):
    """An extension of a NetworkX MultiDiGraph to hold a BEL graph."""

    def __init__(self, lines=None, context=None, lenient=False, complete_origin=False, cache_manager=None,
                 log_stream=None,
                 *attrs, **kwargs):
        """Parses a BEL file from an iterable of strings. This can be a file, file-like, or list of strings.

        :param lines: iterable over lines of BEL data file
        :param context: disease context string
        :type context: str
        :param lenient: if true, allow naked namespaces
        :type lenient: bool
        :param cache_manager: database connection string to cache, pre-built cache manager,
                    or True to use the default
        :type cache_manager: str or pybel.manager.CacheManager
        :param log_stream: a stream to write debug logging to
        :param \*attrs: arguments to pass to :py:meth:`networkx.MultiDiGraph`
        :param \**kwargs: keyword arguments to pass to :py:meth:`networkx.MultiDiGraph`
        """
        nx.MultiDiGraph.__init__(self, *attrs, **kwargs)

        self.last_parse_errors = defaultdict(int)
        self.context = None
        self.metadata_parser = None
        self.bel_parser = None

        if lines is not None:
            self.parse_lines(lines, context, lenient, complete_origin, cache_manager, log_stream)

    def parse_lines(self, lines, context=None, lenient=False, complete_origin=False, cache_manager=None,
                    log_stream=None):
        """Parses an iterable of lines into this graph


        :param lines: iterable over lines of BEL data file
        :param context: disease context string
        :type context: str
        :param lenient: if true, allow naked namespaces
        :type lenient: bool
        :param complete_origin: add corresponding DNA and RNA entities for all proteins
        :param cache_manager: database connection string to cache or pre-built namespace namspace_cache manager
        :type cache_manager: str or pybel.mangager.NamespaceCache
        :param log_stream: a stream to write debug logging to
        """
        if log_stream is not None:
            sh = logging.StreamHandler(stream=log_stream)
            sh.setLevel(5)
            sh.setFormatter(logging.Formatter('%(name)s:%(levelname)s - %(message)s'))
            log.addHandler(sh)

        self.context = context

        docs, definitions, states = split_file_to_annotations_and_definitions(lines)

        if isinstance(cache_manager, CacheManager):
            self.metadata_parser = MetadataParser(cache_manager)
        elif isinstance(cache_manager, str):
            self.metadata_parser = MetadataParser(CacheManager(connection=cache_manager))
        else:
            self.metadata_parser = MetadataParser(CacheManager())

        self.parse_document(docs)

        self.parse_definitions(definitions)

        self.bel_parser = BelParser(graph=self,
                                    valid_namespaces=self.metadata_parser.namespace_dict,
                                    valid_annotations=self.metadata_parser.annotations_dict,
                                    lenient=lenient,
                                    complete_origin=complete_origin)

        self.parse_statements(states)

        log.info('Network has %d nodes and %d edges', self.number_of_nodes(), self.number_of_edges())

        counter = defaultdict(lambda: defaultdict(int))

        for n, d in self.nodes_iter(data=True):
            counter[d['type']][d['namespace'] if 'namespace' in d else 'DEFAULT'] += 1

        for fn, nss in sorted(counter.items()):
            log.debug(' %s: %d', fn, sum(nss.values()))
            for ns, count in sorted(nss.items()):
                log.debug('   %s: %d', ns, count)

    def parse_document(self, document_metadata):
        t = time.time()

        for line_number, line in document_metadata:
            try:
                self.metadata_parser.parseString(line)
            except Exception as e:
                log.error('Line %07d - Critical Failure - %s', line_number, line)
                raise e

        self.graph['document_metadata'] = self.metadata_parser.document_metadata

        log.info('Finished parsing document section in %.02f seconds', time.time() - t)

    def parse_definitions(self, definitions):
        t = time.time()

        for line_number, line in definitions:
            try:
                self.metadata_parser.parseString(line)
            except Exception as e:
                log.critical('Line %07d - Critical Failure - %s', line_number, line)
                raise e

        self.graph['namespace_owl'] = self.metadata_parser.namespace_owl_dict
        self.graph['namespace_url'] = self.metadata_parser.namespace_url_dict
        self.graph['annotation_url'] = self.metadata_parser.annotation_url_dict
        self.graph['annotation_list'] = {e: self.metadata_parser.annotations_dict[e] for e in
                                         self.metadata_parser.annotation_list_list}

        log.info('Finished parsing definitions section in %.02f seconds', time.time() - t)

    def parse_statements(self, statements):
        t = time.time()

        self.bel_parser.language.streamline()
        log.info('Finished streamlining BEL parser in %.02fs', time.time() - t)

        t = time.time()

        self.last_parse_errors = defaultdict(int)

        for line_number, line in statements:
            try:
                self.bel_parser.parseString(line)
            except ParseException:
                log.error('Line %07d - general parser failure: %s', line_number, line)
                self.last_parse_errors['general parser failure'] += 1
            except PyBelWarning as e:
                log.warning('Line %07d - %s', line_number, e)
                self.last_parse_errors[e.__class__.__name__] += 1
            except e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                log.error('Line %07d - general failure: %s - %s: %s', line_number, line, exc_type, exc_value)
                self.last_parse_errors[e.__class__.__name__] += 1

        log.info('Finished parsing statements section in %.02f seconds with %d warnings', time.time() - t,
                 sum(self.last_parse_errors.values()))

        for k, v in sorted(self.last_parse_errors.items()):
            log.debug('  %s: %d', k, v)

    def edges_iter(self, nbunch=None, data=False, keys=False, default=None, **kwargs):
        """Allows for filtering by checking keyword arguments are a subdictionary of each edges' data.
            See :py:meth:`networkx.MultiDiGraph.edges_iter`"""
        for u, v, k, d in nx.MultiDiGraph.edges_iter(self, nbunch=nbunch, data=True, keys=True, default=default):
            if not subdict_matches(d, kwargs):
                continue
            elif keys and data:
                yield u, v, k, d
            elif data:
                yield u, v, d
            elif keys:
                yield u, v, k
            else:
                yield u, v

    def nodes_iter(self, data=False, **kwargs):
        """Allows for filtering by checking keyword arguments are a subdictionary of each nodes' data.
            See :py:meth:`networkx.MultiDiGraph.edges_iter`"""
        for n, d in nx.MultiDiGraph.nodes_iter(self, data=True):
            if not subdict_matches(d, kwargs):
                continue
            elif data:
                yield n, d
            else:
                yield n

    @property
    def document(self):
        return self.graph['document_metadata']

    @property
    def namespace_url(self):
        return self.graph['namespace_url']

    @property
    def namespace_owl(self):
        return self.graph['namespace_owl']

    @property
    def annotation_url(self):
        return self.graph['annotation_url']

    @property
    def annotation_list(self):
        return self.graph['annotation_list']


def to_neo4j(graph, neo_graph, context=None):
    """Uploads a BEL graph to Neo4J graph database using `py2neo`

    :param graph: a BEL Graph
    :type graph: BELGraph
    :param neo_graph: a py2neo graph object, Refer to the
                        `py2neo documentation <http://py2neo.org/v3/database.html#the-graph>`_
                        for how to build this object.
    :type neo_graph: py2neo.Graph
    :param context: a disease context to allow for multiple disease models in one neo4j instance.
                    Each edge will be assigned an attribute :code:`pybel_context` with this value
    :type context: str
    """

    if graph.context is not None:
        context = graph.context

    tx = neo_graph.begin()

    node_map = {}
    for node, data in graph.nodes(data=True):
        node_type = data['type']
        attrs = {k: v for k, v in data.items() if k != 'type'}

        if 'name' in data:
            attrs['value'] = data['name']

        node_map[node] = py2neo.Node(node_type, bel=decanonicalize_node(graph, node), **attrs)

        tx.create(node_map[node])

    for u, v, data in graph.edges(data=True):
        neo_u = node_map[u]
        neo_v = node_map[v]
        rel_type = data['relation']
        attrs = flatten(data)
        if context is not None:
            attrs[PYBEL_CONTEXT_TAG] = str(context)
        rel = py2neo.Relationship(neo_u, rel_type, neo_v, **attrs)
        tx.create(rel)

    tx.commit()


def to_pickle(graph, output):
    """Writes this graph to a pickle object with nx.write_gpickle

    Cast as a nx.MultiDiGraph before outputting because the pickle serializer can't handle the PyParsing elements
    within the BELGraph class.

    :param graph: a BEL graph
    :type graph: BELGraph
    :param output: a file or filename to write to
    """
    nx.write_gpickle(nx.MultiDiGraph(graph), output)


def from_pickle(path):
    """Reads a graph from a gpickle file

    :param path: File or filename to write. Filenames ending in .gz or .bz2 will be uncompressed.
    :type path: file or list
    :rtype: BELGraph
    """
    return BELGraph(data=nx.read_gpickle(path))


def to_json(graph, output):
    """Writes this graph to a node-link JSON object

    :param graph: a BEL graph
    :type graph: BELGraph
    :param output: a write-supporting filelike object
    """
    data = json_graph.node_link_data(graph)
    data['graph']['annotation_list'] = {k: list(sorted(v)) for k, v in data['graph']['annotation_list'].items()}
    json.dump(data, output, ensure_ascii=False)


def from_json(path):
    """Reads graph from node-link JSON Object"""
    with open(os.path.expanduser(path)) as f:
        data = json.load(f)

    for i, node in enumerate(data['nodes']):
        data['nodes'][i]['id'] = tuple(node['id'])

    g = json_graph.node_link_graph(data, directed=True, multigraph=True)
    return BELGraph(data=g)


def to_graphml(graph, output):
    """Writes this graph to GraphML file. Use .graphml extension so Cytoscape can recognize it

    :param graph: a BEL graph
    :type graph: BELGraph
    :param output: a file or filelike object
    """

    g = nx.MultiDiGraph()

    for node, data in graph.nodes(data=True):
        g.add_node(node, json=json.dumps(data))

    for u, v, key, data in graph.edges(data=True, keys=True):
        g.add_edge(u, v, key=key, attr_dict=flatten(data))

    nx.write_graphml(g, output)


def from_graphml(path):
    """Reads a graph from a graphml file

    :param path: File or filename to write
    :type path: file or str
    :rtype: networkx.MultiDiGraph
    """
    reader = GraphMLReader(node_type=str)
    reader.multigraph = True
    g = list(reader(path=path))[0]
    g = expand_edges(g)
    for n in g:
        g.node[n] = json.loads(g.node[n]['json'])
    return g


def to_csv(graph, output):
    """Writes graph to edge list csv

    :param graph: a BEL graph
    :type graph: BELGraph
    :param output: a file or filelike object
    """
    nx.write_edgelist(flatten_graph_data(graph), output, data=True)


def expand_edges(graph):
    """Returns a new graph with expanded edge data dictionaries

    :param graph: nx.MultiDiGraph
    :type graph: BELGraph
    :rtype: BELGraph
    """

    g = BELGraph()

    for node, data in graph.nodes(data=True):
        g.add_node(node, data)

    for u, v, key, data in graph.edges(data=True, keys=True):
        g.add_edge(u, v, key=key, attr_dict=expand_dict(data))

    return g
