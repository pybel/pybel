# -*- coding: utf-8 -*-

from datetime import datetime
from xml.etree import ElementTree as ET

import networkx as nx
import requests
from onto2nx.ontospy import Ontospy
from requests_file import FileAdapter

try:
    from urlparse import urldefrag
except ImportError:
    from urllib.parse import urldefrag

owl_ns = {
    'owl': 'http://www.w3.org/2002/07/owl#',
    'dc': 'http://purl.org/dc/elements/1.1'
}

IRI = 'IRI'
AIRI = 'abbreviatedIRI'


class OWLParser(nx.DiGraph):
    def __init__(self, content=None, file=None, *attrs, **kwargs):
        """Builds a model of an OWL ontology in OWL/XML document using a NetworkX graph

        :param content: The content of an XML file as a string
        :type content: str
        :param file: input OWL file path or file-like object
        :type file: file or str
        """

        nx.DiGraph.__init__(self, *attrs, **kwargs)

        if file is not None:
            self.tree = ET.parse(file)
        elif content is not None:
            self.tree = ET.ElementTree(ET.fromstring(content))
        else:
            raise ValueError('Missing data source (file/content)')

        self.root = self.tree.getroot()
        self.graph['IRI'] = self.root.attrib['ontologyIRI']

        for el in self.root.findall('./owl:Declaration/owl:Class', owl_ns):
            self.add_node(self.get_iri(el.attrib), type="Class")

        for el in self.root.findall('./owl:Declaration/owl:NamedIndividual', owl_ns):
            self.add_node(self.get_iri(el.attrib), type="NamedIndividual")

        for el in self.root.findall('./owl:SubClassOf', owl_ns):
            if len(el) != 2:
                raise ValueError('something weird with SubClassOf: {} {}'.format(el, el.attrib))

            child = self.get_iri(el[0].attrib)

            if any(x in el[1].attrib for x in {IRI, AIRI}):
                parent = self.get_iri(el[1].attrib)
                self.add_edge(child, parent, type='SubClassOf')
            elif el[1].tag == '{http://www.w3.org/2002/07/owl#}ObjectSomeValuesFrom':  # check if ObjectSomeValuesFrom?
                object_property, parent = el[1]
                parent = self.get_iri(parent.attrib)
                relation = self.get_iri(object_property.attrib)
                self.add_edge(child, parent, type=relation)

        for el in self.root.findall('./owl:ClassAssertion', owl_ns):
            a = el.find('./owl:Class', owl_ns)
            if not self.has_iri(a.attrib):
                continue
            a = self.get_iri(a.attrib)

            b = el.find('./owl:NamedIndividual', owl_ns)
            if not self.has_iri(b.attrib):
                continue
            b = self.get_iri(b.attrib)
            self.add_edge(b, a, type="ClassAssertion")

    @property
    def iri(self):
        return self.graph['IRI']

    def has_iri(self, attribs):
        return any(key in {IRI, AIRI} for key in attribs)

    def strip_iri(self, iri):
        return iri.lstrip(self.graph[IRI]).lstrip('#').strip()

    def strip_airi(self, airi):
        l, r = airi.split(':')
        return r

    def get_iri(self, attribs):
        if IRI in attribs:
            return self.strip_iri(attribs[IRI])
        elif AIRI in attribs:
            return self.strip_airi(attribs[AIRI])


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


CREATION_DATE_FMT = '%Y-%m-%dT%H:%M:%S'
PUBLISHED_DATE_FMT = '%Y-%m-%d'
PUBLISHED_DATE_FMT_2 = '%d:%m:%Y %H:%M'


def parse_datetime(s):
    """Tries to parse a datetime object from a standard datetime format or date format"""
    try:
        dt = datetime.strptime(s, CREATION_DATE_FMT)
        return dt
    except:
        try:
            dt = datetime.strptime(s, PUBLISHED_DATE_FMT)
            return dt
        except:
            try:
                dt = datetime.strptime(s, PUBLISHED_DATE_FMT_2)
                return dt
            except:
                raise ValueError('Incorrect datetime format for {}'.format(s))


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
