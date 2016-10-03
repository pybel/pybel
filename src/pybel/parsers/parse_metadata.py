import logging
import re
from configparser import ConfigParser

import requests
from pyparsing import Suppress, ZeroOrMore, White, dblQuotedString, removeQuotes, Word, alphanums, delimitedList
from requests_file import FileAdapter

from .baseparser import BaseParser

log = logging.getLogger(__name__)

__all__ = ['MetadataParser']

W = Suppress(ZeroOrMore(White()))
q = dblQuotedString().setParseAction(removeQuotes)
word = Word(alphanums)
delimitedSet = Suppress('{') + delimitedList(q) + Suppress('}')
delimiters = "=", "|", ":"

# See https://wiki.openbel.org/display/BELNA/Assignment+of+Encoding+%28Allowed+Functions%29+for+BEL+Namespaces
value_map = {
    'G': 'Gene',
    'R': 'RNA',
    'P': 'Protein',
    'M': 'microRNA',
    'A': 'Abundance',
    'B': 'BiologicalProcess',
    'O': 'Pathology',
    'C': 'Complex'
}


class MetadataParser(BaseParser):
    def __init__(self):
        self.document_metadata = {}

        self.namespace_metadata = {}
        self.namespace_dict = {}

        self.annotations_metadata = {}
        self.annotations_dict = {}

        self.document = Suppress('SET') + W + Suppress('DOCUMENT') + word('key') + W + Suppress('=') + W + q('value')

        namespace_tag = Suppress('DEFINE') + W + Suppress('NAMESPACE')
        self.namespace_url = namespace_tag + W + word('name') + W + Suppress('AS') + W + Suppress('URL') + W + q('url')
        self.namespace_list = namespace_tag + W + word('name') + W + Suppress('AS') + W + Suppress(
            'LIST') + W + delimitedSet('values')

        annotation_tag = Suppress('DEFINE') + W + Suppress('ANNOTATION')
        self.annotation_url = annotation_tag + W + word('name') + W + Suppress('AS') + W + Suppress('URL') + W + q(
            'url')
        self.annotation_list = annotation_tag + W + word('name') + W + Suppress('AS') + W + Suppress(
            'LIST') + W + delimitedSet('values')
        self.annotation_pattern = annotation_tag + W + word('name') + W + Suppress('AS') + W + Suppress(
            'PATTERNS') + W + q('value')

        self.document.setParseAction(self.handle_document)
        self.namespace_url.setParseAction(self.handle_namespace_url)
        self.namespace_list.setParseAction(self.handle_namespace_list)
        self.annotation_url.setParseAction(self.handle_annotations_url)
        self.annotation_list.setParseAction(self.handle_annotation_list)
        self.annotation_pattern.setParseAction(self.handle_annotation_pattern)

        self.language = (self.document | self.namespace_url | self.namespace_list |
                         self.annotation_url | self.annotation_list)

    def get_language(self):
        return self.language

    def handle_document(self, s, l, tokens):
        self.document_metadata[tokens['key']] = tokens['value']
        return tokens

    def handle_namespace_url(self, s, l, tokens):
        url = tokens['url']
        name = tokens['name']

        session = requests.Session()
        if url.startswith('file://'):
            session.mount('file://', FileAdapter())
        res = session.get(url)

        config = ConfigParser(delimiters=delimiters, strict=False)
        config.optionxform = lambda option: option
        config.read_file(line.decode('utf-8') for line in res.iter_lines())

        self.namespace_dict[name] = dict(config['Values'])
        self.namespace_metadata[name] = {k: dict(v) for k, v in config.items() if k != 'Values'}

        return tokens

    def handle_annotations_url(self, s, l, tokens):
        url = tokens['url']
        name = tokens['name']

        session = requests.Session()
        if url.startswith('file://'):
            session.mount('file://', FileAdapter())
        res = session.get(url)

        config = ConfigParser(delimiters=delimiters, strict=False)
        config.optionxform = lambda option: option
        config.read_file(line.decode('utf-8') for line in res.iter_lines())

        self.annotations_dict[name] = dict(config['Values'])
        self.annotations_metadata[name] = {k: dict(v) for k, v in config.items() if k != 'Values'}

        return tokens

    def handle_namespace_list(self, s, l, tokens):
        name = tokens['name']
        values = set(tokens['values'])

        self.namespace_metadata[name] = self.transform_document_annotations()
        self.namespace_dict[name] = values

        return tokens

    def handle_annotation_list(self, s, l, tokens):
        name = tokens['name']
        values = set(tokens['values'])

        self.annotations_metadata[name] = self.transform_document_annotations()
        self.annotations_dict[name] = values

        return tokens

    def handle_annotation_pattern(self, s, l, tokens):
        # TODO implement
        return tokens

    # TODO restructure document metadata for internally defined Namespaces and AnnotationLists
    def transform_document_annotations(self):
        return self.document_metadata.copy()


re_identify_definition = re.compile(
    '^DEFINE\s*(?P<defined_element>(NAMESPACE|ANNOTATION))\s*(?P<keyName>.+?)\s+AS\s+(?P<definition_type>(URL|LIST))\s+(?P<definition>.+)$')
"""Regular expression that is used to identify definitions of Namespaces and Annotations."""

definitions_syntax = {
    'Namespace': {
        'NameString': 'name',
        'Keyword': 'keyword',
        'DomainString': 'domain',
        'SpeciesString': 'species',
        'DescriptionString': 'description',
        'VersionString': 'version',
        'CreatedDateTime': 'createdDateTime',
        'QueryValueURL': 'queryValueUrl',
        'UsageString': 'usageDescription',
        'TypeString': 'typeClass'
    },
    'Author': {
        'NameString': 'authorName',
        'CopyrightString': 'authorCopyright',
        'ContactInfoString': 'authorContactInfo'
    },
    'Citation': {
        'NameString': 'citationName',
        'DescriptionString': 'citationDescription',
        'PublishedVersionString': 'citationPublishedVersion',
        'PublishedDate': 'citationPublishedDate',
        'ReferenceURL': 'citationReferenceURL'
    },
    'Processing': {
        'CaseSensitiveFlag': 'processingCaseSensitiveFlag',
        'DelimiterString': 'processingDelimiter',
        'CacheableFlag': 'processingCacheableFlag'
    },
    'Values': None
}
definitions_syntax['AnnotationDefinition'] = definitions_syntax['Namespace']
"""Dictionary that contains the structure of a definition-file for Namespaces or Annotations."""
