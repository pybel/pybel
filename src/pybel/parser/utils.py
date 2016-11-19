# -*- coding: utf-8 -*-

import itertools as itt
import logging
import re
from xml.etree import ElementTree as ET

import networkx as nx
import requests
from pybel.parser import language
from requests_file import FileAdapter

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


owl_ns = {
    'owl': 'http://www.w3.org/2002/07/owl#',
    'dc': 'http://purl.org/dc/elements/1.1'
}


class OWLParser(nx.DiGraph):
    def __init__(self, content=None, file=None, url=None, functions=None, *attrs, **kwargs):
        """Builds a model of an OWL ontology in OWL/XML document using a NetworkX graph
        :param file: input OWL path or filelike object
        """

        nx.DiGraph.__init__(self, *attrs, **kwargs)

        if file is not None:
            self.tree = ET.parse(file)
        elif content is not None:
            self.tree = ET.ElementTree(ET.fromstring(content))
        elif url is not None:
            session = requests.Session()
            if url.startswith('file://'):
                session.mount('file://', FileAdapter())
            res = session.get(url)
            self.tree = ET.ElementTree(ET.fromstring(res.content))
        else:
            raise ValueError('Missing data source (file/content)')

        # if no functions defined, then all elements can be everything
        self.functions = set(functions) if functions is not None else set(language.value_map)

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

    def build_namespace_dict(self):
        return {node: set(self.functions) for node in self.nodes_iter()}
