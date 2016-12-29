# -*- coding: utf-8 -*-

import logging

from pyparsing import Suppress, And, Word, Optional
from pyparsing import pyparsing_common as ppc

from . import language
from .baseparser import BaseParser, word, quote, delimitedSet
from .parse_exceptions import IllegalDocumentMetadataException

log = logging.getLogger('pybel')

__all__ = ['MetadataParser']


class MetadataParser(BaseParser):
    """Parser for the document and definitions section of a BEL document.

    See: http://openbel.org/language/web/version_1.0/bel_specification_version_1.0.html#_define
    """

    def __init__(self, cache_manager, valid_namespaces=None, valid_annotations=None, ):
        """
        :param cache_manager: a namespace namespace_cache manager
        :type cache_manager: pybel.manager.CacheManager
        :param valid_namespaces: dictionary of pre-loaded namespaces {name: set of valid values}
        :type valid_namespaces: dict
        :param valid_annotations: dictionary of pre-loaded annotations {name: set of valid values}
        :type valid_annotations: dict
        """

        self.cache_manager = cache_manager

        self.document_metadata = {}
        self.namespace_dict = {} if valid_namespaces is None else valid_namespaces
        self.annotations_dict = {} if valid_annotations is None else valid_annotations

        self.namespace_url_dict = {}
        self.namespace_owl_dict = {}
        self.annotation_url_dict = {}
        self.annotation_list_list = []

        as_tag = Suppress('AS')
        url_tag = Suppress('URL')
        list_tag = Suppress('LIST')
        owl_tag = Suppress('OWL')
        set_tag = Suppress('SET')
        define_tag = Suppress('DEFINE')

        function_tags = Word(''.join(language.value_map))

        value = quote | ppc.identifier

        self.document = And([set_tag, Suppress('DOCUMENT'), word('key'), Suppress('='), value('value')])

        namespace_tag = And([define_tag, Suppress('NAMESPACE'), ppc.identifier('name'), as_tag])
        self.namespace_url = And([namespace_tag, url_tag, quote('url')])
        self.namespace_owl = And([namespace_tag, owl_tag, Optional(function_tags('functions')), quote('url')])

        annotation_tag = And([define_tag, Suppress('ANNOTATION'), ppc.identifier('name'), as_tag])
        self.annotation_url = And([annotation_tag, url_tag, quote('url')])
        self.annotation_list = And([annotation_tag, list_tag, delimitedSet('values')])
        self.annotation_pattern = And([annotation_tag, Suppress('PATTERN'), quote('value')])

        self.document.setParseAction(self.handle_document)
        self.namespace_url.setParseAction(self.handle_namespace_url)
        self.namespace_owl.setParseAction(self.handle_namespace_owl)
        self.annotation_url.setParseAction(self.handle_annotations_url)
        self.annotation_list.setParseAction(self.handle_annotation_list)
        self.annotation_pattern.setParseAction(self.handle_annotation_pattern)

        self.language = (self.document | self.namespace_url | self.namespace_owl |
                         self.annotation_url | self.annotation_list | self.annotation_pattern)

    def get_language(self):
        return self.language

    def handle_document(self, s, l, tokens):
        key = tokens['key']

        if key not in language.document_keys:
            raise IllegalDocumentMetadataException('Invalid document metadata key: {}'.format(key))

        if key in self.document_metadata:
            log.warning('Tried to overwrite metadata: {}'.format(key))

        self.document_metadata[key] = tokens['value']

        return tokens

    def handle_namespace_url(self, s, l, tokens):
        name = tokens['name']

        if name in self.namespace_dict:
            log.warning('Tried to overwrite namespace: {}'.format(name))
            return tokens

        url = tokens['url']

        terms = self.cache_manager.get_namespace(url)

        if 0 == len(terms):
            raise ValueError("Empty Namespace: {}".format(url))

        self.namespace_dict[name] = terms
        self.namespace_url_dict[name] = url

        return tokens

    def handle_namespace_owl(self, s, l, tokens):
        name = tokens['name']

        if name in self.namespace_dict:
            log.warning('Tried to overwrite owl namespace: {}'.format(name))
            return tokens

        if 'functions' not in tokens:
            functions = set(language.value_map)
        elif not all(x in language.value_map for x in tokens['functions']):
            raise ValueError("Illegal semantic definition: {}".format(tokens['functions']))
        else:
            functions = set(tokens['functions'])

        url = tokens['url']

        terms = self.cache_manager.get_owl_terms(url)

        if 0 == len(terms):
            raise ValueError("Empty ontology: {}".format(url))

        self.namespace_dict[name] = {term: functions for term in terms}
        self.namespace_owl_dict[name] = url

        return tokens

    def handle_annotations_url(self, s, l, tokens):
        name = tokens['name']

        if name in self.annotations_dict:
            log.warning('Tried to overwrite annotation: {}'.format(name))
            return tokens

        url = tokens['url']

        self.annotations_dict[name] = self.cache_manager.get_annotation(url)
        self.annotation_url_dict[name] = url

        return tokens

    def handle_annotation_list(self, s, l, tokens):
        name = tokens['name']

        if name in self.annotations_dict:
            log.warning('Tried to overwrite annotation: {}'.format(name))
            return tokens

        values = set(tokens['values'])

        self.annotations_dict[name] = values
        self.annotation_list_list.append(name)

        return tokens

    def handle_annotation_pattern(self, s, l, tokens):
        # TODO implement
        raise NotImplementedError('Custom annotation regex matching not yet implemented')
