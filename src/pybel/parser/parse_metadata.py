import logging
from configparser import ConfigParser

import requests
from pyparsing import Suppress
from requests_file import FileAdapter

from .baseparser import BaseParser, W, word, quote, delimitedSet

log = logging.getLogger(__name__)

__all__ = ['MetadataParser']

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
    """Parser for the document and definitions section of a BEL document"""

    # TODO add parameters for automatically loaded metadata and values
    # TODO build class that handles connection to namesapce and annotations database
    def __init__(self, namespace_dict=None, annotations_dict=None):
        """
        :param namespace_dict: dictionary of pre-loaded namespaces {name: set of valid values}
        :type namespace_dict: dict
        :param annotations_dict: dictionary of pre-loaded annotations {name: set of valid values}
        :type annotations_dict: dict
        :return:
        """
        self.document_metadata = {}

        self.namespace_metadata = {}
        self.namespace_dict = {} if namespace_dict is None else namespace_dict

        self.annotations_metadata = {}
        self.annotations_dict = {} if annotations_dict is None else annotations_dict

        self.document = Suppress('SET') + W + Suppress('DOCUMENT') + word('key') + W + Suppress('=') + W + quote(
            'value')

        namespace_tag = Suppress('DEFINE') + W + Suppress('NAMESPACE')
        self.namespace_url = namespace_tag + W + word('name') + W + Suppress('AS') + W + Suppress('URL') + W + quote(
            'url')
        self.namespace_list = namespace_tag + W + word('name') + W + Suppress('AS') + W + Suppress(
            'LIST') + W + delimitedSet('values')

        annotation_tag = Suppress('DEFINE') + W + Suppress('ANNOTATION')
        self.annotation_url = annotation_tag + W + word('name') + W + Suppress('AS') + W + Suppress('URL') + W + quote(
            'url')
        self.annotation_list = annotation_tag + W + word('name') + W + Suppress('AS') + W + Suppress(
            'LIST') + W + delimitedSet('values')
        self.annotation_pattern = annotation_tag + W + word('name') + W + Suppress('AS') + W + Suppress(
            'PATTERNS') + W + quote('value')

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
        name = tokens['name']
        if name in self.namespace_dict:
            return tokens

        url = tokens['url']
        session = requests.Session()
        if url.startswith('file://'):
            session.mount('file://', FileAdapter())
        log.debug('Downloading namespaces from {}'.format(url))
        res = session.get(url)
        res.raise_for_status()

        config = ConfigParser(delimiters=delimiters, strict=False)
        config.optionxform = lambda option: option
        config.read_file(line.decode('utf-8') for line in res.iter_lines())

        self.namespace_dict[name] = dict(config['Values'])
        self.namespace_metadata[name] = {k: dict(v) for k, v in config.items() if k != 'Values'}

        return tokens

    def handle_annotations_url(self, s, l, tokens):
        name = tokens['name']
        if name in self.annotations_dict:
            return tokens

        url = tokens['url']
        session = requests.Session()
        if url.startswith('file://'):
            session.mount('file://', FileAdapter())
        log.debug('Downloading annotations from {}'.format(url))
        res = session.get(url)
        res.raise_for_status()

        config = ConfigParser(delimiters=delimiters, strict=False)
        config.optionxform = lambda option: option
        config.read_file(line.decode('utf-8') for line in res.iter_lines())

        self.annotations_dict[name] = dict(config['Values'])
        self.annotations_metadata[name] = {k: dict(v) for k, v in config.items() if k != 'Values'}

        return tokens

    def handle_namespace_list(self, s, l, tokens):
        name = tokens['name']
        if name in self.namespace_dict:
            return tokens

        values = set(tokens['values'])

        self.namespace_metadata[name] = self.transform_document_annotations()
        self.namespace_dict[name] = values

        return tokens

    def handle_annotation_list(self, s, l, tokens):
        name = tokens['name']
        if name in self.annotations_dict:
            return tokens

        values = set(tokens['values'])

        self.annotations_metadata[name] = self.transform_document_annotations()
        self.annotations_dict[name] = values

        return tokens

    def handle_annotation_pattern(self, s, l, tokens):
        # TODO implement
        raise NotImplementedError('Custom annotation regex matching not yet implemented')

    def transform_document_annotations(self):
        return self.document_metadata.copy()


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
