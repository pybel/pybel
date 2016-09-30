import logging
import time

import networkx as nx
import py2neo
import requests
import os

from .parsers.bel_parser import Parser
from .parsers.set_statements import parse_commands, group_statements, sanitize_statement_lines
from .parsers.utils import sanitize_file_lines, split_file_to_annotations_and_definitions

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

    # TODO consider requests-file https://pypi.python.org/pypi/requests-file/1.3.1
    def parse_from_url(self, url):
        """
        Parses a BEL file from URL resource and adds to graph
        :param url: URL to BEL Resource
        :return: self
        :rtype: BELGraph
        """

        response = requests.get(url)

        if response != 200:
            raise Exception('Url not found')

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
        content = sanitize_file_lines(fl)

        definition_lines, statement_lines = split_file_to_annotations_and_definitions(content)

        # TODO: soon.
        # definition_results = handle_definitions(definition_lines)
        # namespace_dict = build_namespace_dictionary(definition_results)

        sanitary_statement_lines = sanitize_statement_lines(statement_lines)
        parsed_commands = parse_commands(sanitary_statement_lines)
        coms = group_statements(parsed_commands)

        log.info('Loaded lines in {:.2f} seconds'.format(time.time() - t))
        t = time.time()

        parser = Parser(graph=self)
        for com in coms:
            parser.reset_metadata()
            parser.set_citation(com['citation'])

            for line in com['notes']:
                if len(line) == 3 and line[0] == 'S':
                    _, key, value = line
                    parser.set_metadata(key, value)
                elif len(line) == 2 and line[0] == 'U':
                    _, key = line
                    parser.unset_metadata(key)
                elif len(line) == 2 and line[0] == 'X':
                    k, expr = line
                    parser.parse(expr)

        log.info('Parsed BEL in {:.2f} seconds'.format(time.time() - t))
        return self

    def to_neo4j(self, neo_graph):
        """
        Uploads to Neo4J graph database usiny `py2neo`
        :param neo_graph:
        :return:
        """
        node_map = {}
        for node, data in self.nodes(data=True):
            node_type = data.pop('type')
            node_map[node] = py2neo.Node(node_type, name=node, **data)

        relationships = []
        for u, v, data in self.edges(data=True):
            neo_u = node_map[u]
            neo_v = node_map[v]

            rel_type = data.pop('relation')
            rel = py2neo.Relationship(neo_u, rel_type, neo_v, **data)
            relationships.append(rel)

        tx = neo_graph.begin()
        for node, neo_node in node_map.items():
            tx.create(neo_node)

        for rel in relationships:
            tx.create(rel)
        tx.commit()
