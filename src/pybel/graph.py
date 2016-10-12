import logging
import os
import time

import networkx as nx
import py2neo
import requests
from pyparsing import ParseException
from requests_file import FileAdapter

from .parser.parse_bel import BelParser
from .parser.parse_exceptions import PyBelException
from .parser.parse_metadata import MetadataParser
from .parser.utils import split_file_to_annotations_and_definitions, flatten, flatten_edges

log = logging.getLogger(__name__)


def from_lines(it):
    """Loads BEL graph from an iterable of strings or file-like object
    :param it: an iterable of strings
    :return a parsed BEL graph
    :rtype: BELGraph
    """

    return BELGraph().parse_from_lines(it)


def from_url(url):
    """Loads a BEL graph from a URL resource
    :param url: a valid URL string
    :type url: str
    :return: a parsed BEL graph
    :rtype BELGraph
    """

    return BELGraph().parse_from_url(url)


def from_path(path):
    """Loads a BEL graph from a file resource
    :param bel: a file path
    :type bel: str
    :return: a parsed BEL graph
    :rtype BELGraph
    """
    with open(os.path.expanduser(path)) as f:
        return from_lines(f)


def from_database(connection):
    """Loads a BEL graph from a database
    :param connection: The string form of the URL is dialect[+driver]://user:password@host/dbname[?key=value..], where dialect is a database name such as mysql, oracle, postgresql, etc., and driver the name of a DBAPI, such as psycopg2, pyodbc, cx_oracle, etc. Alternatively, the URL can be an instance of URL.
    :type connection: str
    :return: a BEL graph loaded from the database
    :rtype: BELGraph

    Example:
    >>> import pybel
    >>> g = pybel.from_database('sqlite://')
    """
    raise NotImplementedError('Loading from database not yet implemented')


class BELGraph(nx.MultiDiGraph):
    """An extension of a NetworkX MultiGraph to hold a BEL graph."""

    def __init__(self, context=None, *attrs, **kwargs):
        nx.MultiDiGraph.__init__(self, *attrs, **kwargs)

        self.bsp = None
        self.mdp = None
        self.context = context

    def clear(self):
        """Clears the content of the graph and its BEL parser"""
        self.bsp.clear()

    def parse_from_path(self, path):
        """Opens a BEL file from a given path and parses it
        :param path: path to BEL file
        :return self
        :rtype BELGraph
        """
        with open(os.path.expanduser(path)) as f:
            return self.parse_from_lines(f)

    def parse_from_url(self, url):
        """Parses a BEL file from URL resource and adds to graph
        :param url: URL to BEL Resource
        :return: self
        :rtype: BELGraph
        """

        session = requests.session()
        if url.startswith('file://'):
            session.mount('file://', FileAdapter())
        response = session.get(url)
        response.raise_for_status()

        return self.parse_from_lines(response.iter_lines())

    def parse_from_lines(self, fl):
        """Parses a BEL file from an iterable of strings. This can be a file, file-like, or list of strings.
        :param fl: iterable over lines of BEL data file
        :return: self
        :rtype: BELGraph
        """
        t = time.time()

        docs, defs, states = split_file_to_annotations_and_definitions(fl)

        self.mdp = MetadataParser()
        for line_number, line in docs:
            try:
                self.mdp.parseString(line)
            except:
                log.error('Failed on [line:{}]: {}'.format(line_number, line))

        log.info('Finished parsing document section in {:.02f} seconds'.format(time.time() - t))
        t = time.time()

        for line_number, line in defs:
            try:
                res = self.mdp.parseString(line)
                if len(res) == 2:
                    log.debug('{}: {}'.format(res[0], res[1]))
                else:
                    log.debug('{}: [{}]'.format(res[0], ', '.join(res[1:])))
            except ParseException as e:
                log.error('General parser failure on [line:{}]: {}'.format(line_number, line))
            except PyBelException as e:
                log.warning('{} [line:{}] {}'.format(e, line_number, line))
            except:
                log.error('General failure [line:{}]: {}'.format(line_number, line))

        log.info('Finished parsing definitions section in {:.02f} seconds'.format(time.time() - t))
        t = time.time()

        self.bsp = BelParser(graph=self, custom_annotations=self.mdp.annotations_dict)

        for line_number, line in states:
            try:
                self.bsp.parseString(line)
            except ParseException as e:
                log.error('General parser failure on [line:{}]: {}'.format(line_number, line))
            except PyBelException as e:
                log.debug('{} on [line:{}]: {}'.format(e, line_number, line))
            except:
                log.error('General failure on [line:{}]: {}'.format(line_number, line))

        log.info('Finished parsing statements section in {:.02f} seconds'.format(time.time() - t))

        return self

    def to_neo4j(self, neo_graph):
        """Uploads to Neo4J graph database usiny `py2neo`

        :param neo_graph:
        :type neo_graph: py2neo.Graph
        """
        node_map = {}
        for i, (node, data) in enumerate(self.nodes(data=True)):
            node_type = data['type']
            attrs = {k: v for k, v in data.items() if k not in ('type', 'name')}

            if 'name' in data:
                attrs['value'] = data['name']

            node_map[node] = py2neo.Node(node_type, name=str(i), **attrs)

        relationships = []
        for u, v, data in self.edges(data=True):
            neo_u = node_map[u]
            neo_v = node_map[v]
            rel_type = data['relation']
            attrs = flatten(data)
            if self.context is not None:
                attrs['pybel_context'] = str(self.context)
            rel = py2neo.Relationship(neo_u, rel_type, neo_v, **attrs)
            relationships.append(rel)

        tx = neo_graph.begin()
        for neo_node in node_map.values():
            tx.create(neo_node)

        for rel in relationships:
            tx.create(rel)
        tx.commit()

    def to_pickle(self, output):
        """Writes this graph to a pickle object with nx.write_gpickle"""
        nx.write_gpickle(flatten_edges(self), output)
