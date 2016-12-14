# -*- coding: utf-8 -*-

import itertools as itt
import logging
import re
from xml.etree import ElementTree as ET

import networkx as nx
import requests
from requests_file import FileAdapter

from pybel.parser import language
import ontospy
log = logging.getLogger('pybel')

re_match_bel_header = re.compile("(SET\s+DOCUMENT|DEFINE\s+NAMESPACE|DEFINE\s+ANNOTATION)")


def sanitize_file_lines(f):
    """Enumerates a line iterator and returns the pairs of (line number, line) that are cleaned"""
    it = (line.strip() for line in f)
    it = filter(lambda i_l: i_l[1] and not i_l[1].startswith('#'), enumerate(it, start=1))
    it = iter(it)

    for line_number, line in it:
        if line.endswith('\\'):
            log.log(4, 'Multiline quote starting on line: %d', line_number)
            line = line.strip('\\').strip()
            next_line_number, next_line = next(it)
            while next_line.endswith('\\'):
                log.log(3, 'Extending line: %s', next_line)
                line += " " + next_line.strip('\\').strip()
                next_line_number, next_line = next(it)
            line += " " + next_line.strip()
            log.log(3, 'Final line: %s', line)

        elif 1 == line.count('"'):
            log.log(4, 'PyBEL013 Missing new line escapes [line: %d]', line_number)
            next_line_number, next_line = next(it)
            next_line = next_line.strip()
            while not next_line.endswith('"'):
                log.log(3, 'Extending line: %s', next_line)
                line = '{} {}'.format(line.strip(), next_line)
                next_line_number, next_line = next(it)
                next_line = next_line.strip()
            line = '{} {}'.format(line, next_line)
            log.log(3, 'Final line: %s', line)

        comment_loc = line.rfind(' //')
        if 0 <= comment_loc:
            line = line[:comment_loc]

        yield line_number, line


def split_file_to_annotations_and_definitions(file):
    """Enumerates a line iterable and splits into 3 parts"""
    content = list(sanitize_file_lines(file))

    end_document_section = 1 + max(j for j, (i, l) in enumerate(content) if l.startswith('SET DOCUMENT'))
    end_definitions_section = 1 + max(j for j, (i, l) in enumerate(content) if re_match_bel_header.match(l))

    log.info('File length: %d lines', len(content))
    documents = content[:end_document_section]
    definitions = content[end_document_section:end_definitions_section]
    statements = content[end_definitions_section:]

    return documents, definitions, statements


def check_stability(ns_dict, ns_mapping):
    """Check the stability of namespace mapping

    :param ns_dict: dict of {name: set of values}
    :param ns_mapping: dict of {name: {value: (other_name, other_value)}}
    :return: if the mapping is stable
    :rtype: Boolean
    """
    flag = True
    for ns, kv in ns_mapping.items():
        if ns not in ns_dict:
            log.warning('missing namespace %s', ns)
            flag = False
            continue
        for k, (k_ns, v_val) in kv.items():
            if k not in ns_dict[ns]:
                log.warning('missing value %s', k)
                flag = False
            if k_ns not in ns_dict:
                log.warning('missing namespace link %s', k_ns)
                flag = False
            elif v_val not in ns_dict[k_ns]:
                log.warning('missing value %s in namespace %s', v_val, k_ns)
                flag = False
    return flag


def list2tuple(l):
    """turns a nested list to a nested tuple"""
    if not isinstance(l, list):
        return l
    else:
        return tuple(list2tuple(e) for e in l)


def subdict_matches(a, b):
    """Checks if all the keys in b are in a, and that their values match

    :param a: a dictionary
    :type a: dict
    :param b: a dictionary
    :type b: dict
    :return: if all keys in b are in a and their values match
    :rtype: bool
    """
    for k, v in b.items():
        if k not in a:
            return False
        elif isinstance(v, (str, dict)) and a[k] != v:
            return False
        elif isinstance(v, (list, set, tuple)) and a[k] not in v:
            return False
        elif not isinstance(v, (str, list, set, dict, tuple)):
            raise ValueError('invalid value: {}'.format(v))
    return True


def any_subdict_matches(a, b):
    """Checks if dictionary b matches one of the subdictionaries of a

    :param a: dictionary of dictionaries
    :param b: dictionary
    :return: if dictionary b matches one of the subdictionaries of a
    :rtype: bool
    """
    return any(subdict_matches(sd, b) for sd in a.values())


def cartesian_dictionary(d):
    """takes a dictionary of sets and provides subdicts

    :param d: a dictionary of sets
    :type d: dict
    :rtype: list
    """
    q = {}
    for key in d:
        q[key] = {(key, value) for value in d[key]}

    res = []
    for values in itt.product(*q.values()):
        res.append(dict(values))

    return res


def handle_debug(fmt):
    """logging hook for pyparsing

    :param fmt: a format string with {s} for string, {l} for location, and {t} for tokens
    """

    def handle(s, l, t):
        log.log(5, fmt.format(s=s, location=l, tokens=t))
        return t

    return handle


def ensure_quotes(s):
    """Quote a string that isn't solely alphanumeric

    :param s: a string
    :type s: str
    :rtype: str
    """
    return '"{}"'.format(s) if not s.isalnum() else s


conversion_service = "http://owl.cs.manchester.ac.uk/converter/convert?format=OWL/XML&ontology={}"


# TODO logging of download??
# TODO insert all relevant metadata into owl.graph (networkx graph annotations)
def parse_owl(url, fail=False):
    """

    :param url:
    :param functions:
    :return:
    :rtype: OWLParser
    """

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
                g.add_edge(instance.locale, cls.locale, type='ClassAssertion')

        return g


owl_ns = {
    'owl': 'http://www.w3.org/2002/07/owl#',
    'dc': 'http://purl.org/dc/elements/1.1'
}

IRI = 'IRI'
AIRI = 'abbreviatedIRI'


class OWLParser(nx.DiGraph):
    def __init__(self, content=None, file=None, functions=None, *attrs, **kwargs):
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

        # if no functions defined, then all elements can be everything
        self.functions = set(functions) if functions is not None else set(language.value_map)

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
            if not has_iri(a.attrib):
                continue
            a = self.get_iri(a.attrib)

            b = el.find('./owl:NamedIndividual', owl_ns)
            if not has_iri(b.attrib):
                continue
            b = self.get_iri(b.attrib)
            self.add_edge(b, a, type="ClassAssertion")


    def strip_iri(self, iri):
        return iri.lstrip(self.graph[IRI]).lstrip('#').strip()

    def get_iri(self, attribs):
        if IRI in attribs:
            return self.strip_iri(attribs[IRI])
        elif AIRI in attribs:
            return strip_airi(attribs[AIRI])

    @property
    def iri(self):
        return self.graph['IRI']

def has_iri(attribs):
    return any(key in {IRI, AIRI} for key in attribs)

def strip_airi(airi):
    l, r = airi.split(':')
    return r
