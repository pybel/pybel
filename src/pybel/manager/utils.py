# -*- coding: utf-8 -*-

import networkx as nx
from requests.compat import urldefrag

from ..resources.utils import download
from ..utils import parse_datetime


def parse_owl(url):
    """Downloads and parses an OWL resource in OWL/XML or any format supported by onto2nx/ontospy package.
    Is a thin wrapper around :func:`parse_owl_pybel` and :func:`parse_owl_rdf`.
    
    :param str url: The URL to the OWL resource
    :return: A directional graph representing the OWL document's hierarchy
    :rtype: networkx.DiGraph
    """
    try:
        return parse_owl_xml(url)
    except:
        return parse_owl_rdf(url)


def parse_owl_xml(url):
    """Downloads and parses an OWL resource in OWL/XML format using :class:`onto2nx.parse_owl_xml.OWLParser`
    
    :param str url: The URL to the OWL resource
    :return: A directional graph representing the OWL document's hierarchy
    :rtype: networkx.DiGraph
    """
    from onto2nx.parse_owl_xml import OWLParser

    res = download(url)
    rv = OWLParser(content=res.content)

    return rv


def parse_owl_rdf(url):
    """Downloads and parses an OWL resource in OWL/RDF format

    :param str url: The URL to the OWL resource
    :return: A directional graph representing the OWL document's hierarchy
    :rtype: networkx.DiGraph
    """
    from onto2nx.ontospy import Ontospy

    rv = nx.DiGraph(IRI=url)
    o = Ontospy(url)

    for cls in o.classes:
        rv.add_node(cls.locale, type='Class')

        for parent in cls.parents():
            rv.add_edge(cls.locale, parent.locale, type='SubClassOf')

        for instance in cls.instances():
            _, frag = urldefrag(instance)
            rv.add_edge(frag, cls.locale, type='ClassAssertion')

    return rv


def extract_shared_required(config, definition_header='Namespace'):
    """Gets the required annotations shared by BEL namespace and annotation resource documents

    :param dict config: The configuration dictionary representing a BEL resource
    :param str definition_header: ``Namespace`` or ``AnnotationDefinition``
    :rtype: dict
    """
    return {
        'keyword': config[definition_header]['Keyword'],
        'created': parse_datetime(config[definition_header]['CreatedDateTime']),
        'author': config['Author']['NameString'],
        'citation': config['Citation']['NameString']
    }


def update_insert_values(bel_resource, m, d):
    for database_column, (section, key) in m.items():
        if section in bel_resource and key in bel_resource[section]:
            d[database_column] = bel_resource[section][key]


def extract_shared_optional(bel_resource, definition_header='Namespace'):
    """Gets the optional annotations shared by BEL namespace and annotation resource documents
    
    :param dict bel_resource: A configuration dictionary representing a BEL resource
    :param str definition_header: ``Namespace`` or ``AnnotationDefinition``
    :rtype: dict
    """
    shared_mapping = {
        'description': (definition_header, 'DescriptionString'),
        'version': (definition_header, 'VersionString'),
        'license': ('Author', 'CopyrightString'),
        'contact': ('Author', 'ContactInfoString'),
        'citation_description': ('Citation', 'DescriptionString'),
        'citation_version': ('Citation', 'PublishedVersionString'),
        'citation_url': ('Citation', 'ReferenceURL')
    }

    result = {}

    update_insert_values(bel_resource, shared_mapping, result)

    if 'PublishedDate' in bel_resource['Citation']:
        result['citation_published'] = parse_datetime(bel_resource['Citation']['PublishedDate'])

    return result


def int_or_str(v):
    """Safe converts an string represent an integer to an integer. If it's none, returns none

    :param v:
    :return:
    """
    if v is None:
        return
    try:
        return int(v)
    except Exception:
        return v
