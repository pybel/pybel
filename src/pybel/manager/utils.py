from xml.etree import ElementTree as ET

import networkx as nx
import ontospy
import requests
from rdflib.term import urldefrag
from requests_file import FileAdapter

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
    session = requests.Session()
    if url.startswith('file://'):
        session.mount('file://', FileAdapter())
    res = session.get(url)

    try:
        owl = OWLParser(content=res.content)
        return owl
    except:
        g = nx.DiGraph(IRI=url)
        o = ontospy.Ontospy(url)

        for cls in o.classes:
            g.add_node(cls.locale, type='Class')

            for parent in cls.parents():
                g.add_edge(cls.locale, parent.locale, type='SubClassOf')

            for instance in cls.instances():
                _, frag = urldefrag(instance)
                g.add_edge(frag, cls.locale, type='ClassAssertion')

        return g
