# -*- coding: utf-8 -*-

import networkx as nx
import requests
from onto2nx.ontospy import Ontospy
from onto2nx.parse_owl_xml import OWLParser
from requests.compat import urldefrag
from requests_file import FileAdapter

from ..utils import parse_datetime


def parse_owl(url):
    try:
        return parse_owl_pybel(url)
    except:
        return parse_owl_rdf(url)


def parse_owl_pybel(url):
    session = requests.Session()
    session.mount('file://', FileAdapter())
    res = session.get(url)
    owl = OWLParser(content=res.content)
    return owl


def parse_owl_rdf(iri):
    g = nx.DiGraph(IRI=iri)
    o = Ontospy(iri)

    for cls in o.classes:
        g.add_node(cls.locale, type='Class')

        for parent in cls.parents():
            g.add_edge(cls.locale, parent.locale, type='SubClassOf')

        for instance in cls.instances():
            _, frag = urldefrag(instance)
            g.add_edge(frag, cls.locale, type='ClassAssertion')

    return g


def extract_shared_required(config, definition_header='Namespace'):
    """

    :param config:
    :param definition_header: 'Namespace' or 'AnnotationDefinition'
    :return:
    """
    return {
        'keyword': config[definition_header]['Keyword'],
        'created': parse_datetime(config[definition_header]['CreatedDateTime']),
        'author': config['Author']['NameString'],
        'citation': config['Citation']['NameString']
    }


def extract_shared_optional(config, definition_header='Namespace'):
    s = {
        'description': (definition_header, 'DescriptionString'),
        'version': (definition_header, 'VersionString'),
        'license': ('Author', 'CopyrightString'),
        'contact': ('Author', 'ContactInfoString'),
        'citation_description': ('Citation', 'DescriptionString'),
        'citation_version': ('Citation', 'PublishedVersionString'),
        'citation_url': ('Citation', 'ReferenceURL')
    }

    x = {}

    for database_column, (section, key) in s.items():
        if section in config and key in config[section]:
            x[database_column] = config[section][key]

    if 'PublishedDate' in config['Citation']:
        x['citation_published'] = parse_datetime(config['Citation']['PublishedDate'])

    return x
