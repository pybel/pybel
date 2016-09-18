import io
import logging
import time

import networkx as nx
import py2neo
import requests

from .parsers import language
from .parsers import split_file_to_annotations_and_definitions
from .parsers.set_statements import parse_commands, group_statements, sanitize_statement_lines
from .parsers.tokenizer import Parser
from .parsers.utils import sanitize_file_lines

log = logging.getLogger(__name__)


def from_url(url):
    """
    Parses a BEL file from URL resource
    :param url: URL to BEL resource
    :return: a BEL MultiGraph
    :rtype BELGraph
    """
    return BELGraph().parse_from_url(url)


def from_file(fl):
    """
    Parses a BEL file from a file-like object
    :param fl: file-like object backed by BEL data
    :return: a BEL MultiGraph
    :rtype BELGraph
    """
    return BELGraph().parse_from_file(fl)


class BELGraph(nx.MultiDiGraph):
    """
    An extension of a NetworkX MultiGraph to hold a BEL graph.
    """

    def __init__(self, *attrs, **kwargs):
        super().__init__(self, *attrs, **kwargs)

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

        return self.parse_from_file(io.StringIO(response.text))


    # TODO break up into smaller commands with tests
    def parse_from_file(self, fl):
        """
        Parses a BEL file from a file-like object and adds to graph
        :param fl: file-like object backed by BEL data
        :return: self
        :rtype: BELGraph
        """
        t = time.time()
        content = sanitize_file_lines(fl)

        definition_lines, statement_lines = split_file_to_annotations_and_definitions(content)

        # definition_results = handle_definitions(definition_lines)

        sanitary_statement_lines = sanitize_statement_lines(statement_lines)
        parsed_commands = parse_commands(sanitary_statement_lines)
        coms = group_statements(parsed_commands)

        print('Time: {:.2f} seconds'.format(time.time() - t))

        parser = Parser()
        for com in coms:
            citation = com['citation']
            lines = com['notes']

            log.debug(citation)
            d = {}

            for line in lines:

                if len(line) == 3 and line[0] == 'S':
                    _, key, value = line
                    d[key] = value.strip('"').strip()
                elif len(line) == 2 and line[0] == 'X':
                    k, expr = line

                    tokens = parser.tokenize(expr)
                    if tokens is None:
                        continue

                    s, p, o = tokens

                    if s[0] in language.functions and o[0] in language.functions:
                        s_ns, s_name = s[1]
                        o_ns, o_name = o[1]

                        s_can = '{}:{}'.format(s_ns, s_name)
                        o_can = '{}:{}'.format(o_ns, o_name)

                        if s_can not in self:
                            self.add_node(s_can, type=s[0], name=s_name, namespace=s_ns)
                            log.debug('added {}:{}'.format(s[0], s_can))

                        if o_can not in self:
                            self.add_node(o_can, type=o[0], name=s_name, namespace=o_ns)
                            log.debug('added {}:{}'.format(o[0], o_can))

                        attrs = d.copy()
                        attrs['relation'] = p

                        for key in citation:
                            attrs['citation_{}'.format(key)] = citation[key]

                        log.debug('added {}{}{}'.format(s_can, p, o_can))

                        self.add_edge(s_can, o_can, attr_dict=attrs)
        return self

    def to_neo4j(self, neo_graph: py2neo.Graph):
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
