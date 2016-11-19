import collections
import logging
import xml.etree.ElementTree as ET
from collections import defaultdict
from configparser import ConfigParser

import networkx as nx
import requests
from requests_file import FileAdapter

log = logging.getLogger(__name__)


def download_url(url):
    """Downloads and parses a config file from url"""
    session = requests.Session()
    if url.startswith('file://'):
        session.mount('file://', FileAdapter())
    res = session.get(url)

    lines = [line.decode('utf-8', errors='ignore').strip() for line in res.iter_lines()]

    value_line = 1 + max(i for i, line in enumerate(lines) if '[Values]' == line.strip())

    metadata_config = ConfigParser(strict=False)
    metadata_config.optionxform = lambda option: option
    metadata_config.read_file(lines[:value_line])

    delimiter = metadata_config['Processing']['DelimiterString']

    value_dict = {}
    for line in lines[value_line:]:
        sline = line.rsplit(delimiter, 1)
        key = sline[0].strip()

        value_dict[key] = sline[1].strip() if len(sline) == 2 else None

    res = {}
    res.update({k: dict(v) for k, v in metadata_config.items()})
    res['Values'] = value_dict

    return res


def expand_dict(flat_dict, sep='_'):
    """Expands a flattened dictionary
    :param flat_dict: a nested dictionary that has been flattened so the keys are composite and
    """
    res = {}
    rdict = defaultdict(list)

    for flat_key, value in flat_dict.items():
        key = flat_key.split(sep, 1)
        if 1 == len(key):
            res[key[0]] = value
        else:
            rdict[key[0]].append((key[1:], value))

    for k, v in rdict.items():
        res[k] = expand_dict({ik: iv for (ik,), iv in v})

    return res


def flatten(d, parent_key='', sep='_'):
    """Flattens a nested dictionary

    Borrowed from http://stackoverflow.com/a/6027615
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        elif isinstance(v, (set, list)):
            items.append((new_key, ','.join(v)))
        else:
            items.append((new_key, v))
    return dict(items)


def flatten_graph_data(graph):
    """Returns a new graph with flattened edge data dictionaries

    :param graph:
    :type graph: nx.MultiDiGraph
    :rtype: nx.MultiDiGraph
    """

    g = nx.MultiDiGraph()

    for node, data in graph.nodes(data=True):
        g.add_node(node, data)

    for u, v, key, data in graph.edges(data=True, keys=True):
        g.add_edge(u, v, key=key, attr_dict=flatten(data))

    return g


owl_ns = {
    'owl': 'http://www.w3.org/2002/07/owl#',
    'dc': 'http://purl.org/dc/elements/1.1'
}


class OWLParser(nx.DiGraph):
    def __init__(self, content=None, file=None, *attrs, **kwargs):
        """Builds a model of an OWL ontology in OWL/XML document using a NetworkX graph
        :param file: input OWL path or filelike object
        """

        nx.DiGraph.__init__(self, *attrs, **kwargs)

        if file is not None:
            self.tree = ET.parse(file)
        elif content is not None:
            self.tree = ET.ElementTree(ET.fromstring(content))
        else:
            raise ValueError('Missing data source (file/content)')

        self.root = self.tree.getroot()
        self.name_url = self.root.attrib['ontologyIRI']

        labels = {}

        for el in self.root.findall('./owl:AnnotationAssertion', owl_ns):
            if len(el) == 3:
                prop, iri, lit = el

                if '{http://www.w3.org/XML/1998/namespace}lang' in lit.attrib:
                    if 'en' != lit.attrib['{http://www.w3.org/XML/1998/namespace}lang']:
                        log.debug('non-english detected')
                        continue

                labels[iri.text.lstrip('#').strip()] = lit.text.strip()

        for el in self.root.findall('./owl:SubClassOf', owl_ns):
            children = el.findall('./owl:Class[@IRI]', owl_ns)
            if len(children) == 2:
                sub, sup = children

                u = sub.attrib['IRI'].lstrip('#').strip()
                v = sup.attrib['IRI'].lstrip('#').strip()

                if u in labels:
                    u = labels[u]
                if v in labels:
                    v = labels[v]

                self.add_edge(u, v)

    def ensure_metadata(self):
        email = self.root.find('''./owl:Annotation/owl:AnnotationProperty[@IRI='#email']/../owl:Literal''', owl_ns)
        if not email:
            raise Exception('Missing #email document Annotation. Add this custom metadata with protege')
        self.graph['email'] = email.text.strip()

        required_dc = 'title', 'subject', 'creator', 'description', 'date'

        for dc_term in required_dc:
            self.graph[dc_term] = self.find_dc(dc_term, owl_ns)

        if not all(key in self.graph and self.graph[key] for key in required_dc):
            raise Exception(
                'Missing DC terms in Annotation section. Required: {}. See purl.org/dc/elements/1.1/. Found {}'.format(
                    required_dc, self.graph))

    def find_dc(self, term, ns):
        search_string1 = './owl:Annotation/owl:AnnotationProperty[@abbreviatedIRI="dc:{}"]/../owl:Literal'
        for el in self.root.findall(search_string1.format(term), ns):
            return el.text.strip()

        search_string2 = './owl:Annotation/owl:AnnotationProperty[@IRI="http://purl.org/dc/elements/1.1/{}"]/../owl:Literal'
        for el in self.root.findall(search_string2.format(term), ns):
            return el.text.strip()
