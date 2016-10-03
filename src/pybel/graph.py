import logging
import os
import time

import networkx as nx
import py2neo
import requests
from requests_file import FileAdapter

from .parsers.parse_bel import BelParser
from .parsers.parse_control import ControlParser
from .parsers.parse_metadata import MetadataParser
from .parsers.utils import split_file_to_annotations_and_definitions

log = logging.getLogger(__name__)


def from_bel(bel):
    """
    Parses a BEL file from URL or file resource
    :param bel: URL or file path to BEL resource
    :type bel: str
    :return: a BEL MultiGraph
    :rtype BELGraph
    """
    if bel.startswith('http'):
        return BELGraph().parse_from_url(bel)
    with open(os.path.expanduser(bel)) as f:
        return BELGraph().parse_from_file(f)


class BELGraph(nx.MultiDiGraph):
    """
    An extension of a NetworkX MultiGraph to hold a BEL graph.
    """

    def __init__(self, *attrs, **kwargs):
        nx.MultiDiGraph.__init__(self, *attrs, **kwargs)

        self.bsp = None
        self.csp = None
        self.mdp = None

    def parse_from_url(self, url):
        """
        Parses a BEL file from URL resource and adds to graph
        :param url: URL to BEL Resource
        :return: self
        :rtype: BELGraph
        """

        session = requests.session()
        if url.starts('file://'):
            session.mount('file://', FileAdapter())
        response = session.get(url)

        if response.status_code != 200:
            raise Exception('URL not found')

        return self.parse_from_file(response.iter_lines())

    # TODO break up into smaller commands with tests
    def parse_from_file(self, fl):
        """
        Parses a BEL file from a file-like object and adds to graph
        :param fl: iterable over lines of BEL data file
        :return: self
        :rtype: BELGraph
        """
        t = time.time()

        docs, defs, states = split_file_to_annotations_and_definitions(fl)

        mdp = MetadataParser()
        for line in docs:
            try:
                mdp.parse(line)
            except:
                log.error('Failed: {}'.format(line))

        log.info('Finished parsing document section in {} seconds'.format(time.time() - t))
        t = time.time()

        for line in defs:
            try:
                mdp.parse(line)
            except:
                log.error('Failed: {}'.format(line))

        log.info('Finished parsing definitions section in {} seconds'.format(time.time() - t))
        t = time.time()

        bsp = BelParser(graph=self)
        csp = ControlParser(custom_annotations=mdp.annotations_dict)

        stmt = csp.get_language() | bsp.get_language()
        for line in states:
            try:
                stmt.parseString(line)
            except:
                log.error('Failed: {}'.format(line))

        log.info('Finished parsing statements section in {} seconds'.format(time.time() - t))

        return self

    def to_neo4j(self, neo_graph):
        """
        Uploads to Neo4J graph database usiny `py2neo`
        :param neo_graph:
        :return:
        """
        node_map = {}
        for i, (node, data) in enumerate(self.nodes(data=True)):
            node_type = data['type']
            attrs = {k: v for k, v in data.items() if k != 'type'}
            node_map[node] = py2neo.Node(node_type, name=str(i), **attrs)

        relationships = []
        for u, v, data in self.edges(data=True):
            neo_u = node_map[u]
            neo_v = node_map[v]

            rel_type = data['relation']

            attrs = {}
            for k in ('subject', 'object'):
                if k == 'relation' or k not in data or not data[k]:
                    continue
                for key, value in data[k].items():
                    if isinstance(value, dict):
                        for k2, v2 in value.items():
                            attrs['subject_{}_{}'.format(key, k2)] = v2
                    else:
                        attrs['subject_{}'.format(key)] = value

            rel = py2neo.Relationship(neo_u, rel_type, neo_v, **attrs)
            relationships.append(rel)

        tx = neo_graph.begin()
        for neo_node in node_map.values():
            tx.create(neo_node)

        for rel in relationships:
            tx.create(rel)
        tx.commit()
