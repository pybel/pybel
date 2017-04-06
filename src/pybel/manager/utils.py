# -*- coding: utf-8 -*-

import networkx as nx
from onto2nx.ontospy import Ontospy
from onto2nx.parse_owl_xml import OWLParser
from requests.compat import urldefrag

from ..utils import parse_datetime, download


def parse_owl(url):
    """Downloads and parses an OWL resource in OWL/XML or any format supported by onto2nx/ontospy package.
    Is a thin wrapper around :func:`parse_owl_pybel` and :func:`parse_owl_rdf`.
    
    :param url: The URL to the OWL resource
    :type url: str
    :return: A directional graph representing the OWL document's hierarchy
    :rtype: networkx.DiGraph
    """
    try:
        return parse_owl_pybel(url)
    except:
        return parse_owl_rdf(url)


def parse_owl_pybel(url):
    """Downloads and parses an OWL resource in OWL/XML format
    
    :param url: The URL to the OWL resource
    :type url: str 
    :return: A directional graph representing the OWL document's hierarchy
    :rtype: networkx.DiGraph
    """
    res = download(url)
    owl = OWLParser(content=res.content)
    return owl


def parse_owl_rdf(iri):
    """Downloads and parses an OWL resource in OWL/RDF format

    :param url: The URL to the OWL resource
    :type url: str 
    :return: A directional graph representing the OWL document's hierarchy
    :rtype: networkx.DiGraph
    """
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
    """Gets the required annotations shared by BEL namespace and annotation resource documents

    :param config: The configuration dictionary representing a BEL resource
    :type config: dict
    :param definition_header: ``Namespace`` or ``AnnotationDefinition``
    :type definition_header: str
    :return:
    """
    return {
        'keyword': config[definition_header]['Keyword'],
        'created': parse_datetime(config[definition_header]['CreatedDateTime']),
        'author': config['Author']['NameString'],
        'citation': config['Citation']['NameString']
    }


def extract_shared_optional(config, definition_header='Namespace'):
    """Gets the optional annotations shared by BEL namespace and annotation resource documents
    
    :param config: A configuration dictionary representing a BEL resource
    :type config: dict
    :param definition_header: ``Namespace`` or ``AnnotationDefinition``
    :type definition_header: str
    :return: 
    """
    s = {
        'description': (definition_header, 'DescriptionString'),
        'version': (definition_header, 'VersionString'),
        'license': ('Author', 'CopyrightString'),
        'contact': ('Author', 'ContactInfoString'),
        'citation_description': ('Citation', 'DescriptionString'),
        'citation_version': ('Citation', 'PublishedVersionString'),
        'citation_url': ('Citation', 'ReferenceURL')
    }

    result = {}

    for database_column, (section, key) in s.items():
        if section in config and key in config[section]:
            result[database_column] = config[section][key]

    if 'PublishedDate' in config['Citation']:
        result['citation_published'] = parse_datetime(config['Citation']['PublishedDate'])

    return result
