# -*- coding: utf-8 -*-

"""
Metadata Parser
~~~~~~~~~~~~~~~
This module supports the relation parser by handling statements.
"""

import logging

from pyparsing import Suppress, And, Word, Optional, MatchFirst
from pyparsing import pyparsing_common as ppc

from . import language
from .baseparser import BaseParser, word, quote, delimitedSet
from .parse_exceptions import InvalidMetadataException
from ..constants import BEL_KEYWORD_AS, BEL_KEYWORD_URL, BEL_KEYWORD_LIST, BEL_KEYWORD_OWL, BEL_KEYWORD_SET, \
    BEL_KEYWORD_DEFINE, BEL_KEYWORD_NAMESPACE, BEL_KEYWORD_ANNOTATION, BEL_KEYWORD_DOCUMENT, BEL_KEYWORD_PATTERN, \
    DOCUMENT_KEYS

log = logging.getLogger('pybel')

__all__ = ['MetadataParser']

as_tag = Suppress(BEL_KEYWORD_AS)
url_tag = Suppress(BEL_KEYWORD_URL)
list_tag = Suppress(BEL_KEYWORD_LIST)
owl_tag = Suppress(BEL_KEYWORD_OWL)
set_tag = Suppress(BEL_KEYWORD_SET)
define_tag = Suppress(BEL_KEYWORD_DEFINE)

function_tags = Word(''.join(language.belns_encodings))

value = quote | ppc.identifier


class MetadataParser(BaseParser):
    """Parser for the document and definitions section of a BEL document.

    .. seealso::

        BEL 1.0 Specification for the `DEFINE <http://openbel.org/language/web/version_1.0/bel_specification_version_1.0.html#_define>`_ keyword
    """

    def __init__(self, cache_manager, valid_namespaces=None, valid_annotations=None, namespace_re=None,
                 annotations_re=None):
        """
        :param cache_manager: a namespace namespace_cache manager
        :type cache_manager: pybel.manager.CacheManager
        :param valid_namespaces: dictionary of pre-loaded namespaces {name: set of valid values}
        :type valid_namespaces: dict
        :param valid_annotations: dictionary of pre-loaded annotations {name: set of valid values}
        :type valid_annotations: dict
        :param namespace_re: a dictionary of pre-loaded namespace regular expressions {name: regex string}
        :type namespace_re: dict
        :param annotations_re: a dictionary of pre-loaded annotation regular expressions {name: regex string}
        :type annotations_re: dict
        """

        self.cache_manager = cache_manager

        self.namespace_dict = {} if valid_namespaces is None else valid_namespaces
        self.annotations_dict = {} if valid_annotations is None else valid_annotations
        self.namespace_re = {} if namespace_re is None else namespace_re
        self.annotations_re = {} if annotations_re is None else annotations_re

        self.document_metadata = {}

        self.namespace_url_dict = {}
        self.namespace_owl_dict = {}
        self.annotation_url_dict = {}
        self.annotations_owl_dict = {}
        self.annotation_list_list = []

        self.document = And([set_tag, Suppress(BEL_KEYWORD_DOCUMENT), word('key'), Suppress('='), value('value')])

        namespace_tag = And([define_tag, Suppress(BEL_KEYWORD_NAMESPACE), ppc.identifier('name'), as_tag])
        self.namespace_url = And([namespace_tag, url_tag, quote('url')])
        self.namespace_owl = And([namespace_tag, owl_tag, Optional(function_tags('functions')), quote('url')])
        self.namespace_pattern = And([namespace_tag, Suppress(BEL_KEYWORD_PATTERN), quote('value')])

        annotation_tag = And([define_tag, Suppress(BEL_KEYWORD_ANNOTATION), ppc.identifier('name'), as_tag])
        self.annotation_url = And([annotation_tag, url_tag, quote('url')])
        self.annotation_owl = And([annotation_tag, owl_tag, quote('url')])
        self.annotation_list = And([annotation_tag, list_tag, delimitedSet('values')])
        self.annotation_pattern = And([annotation_tag, Suppress(BEL_KEYWORD_PATTERN), quote('value')])

        self.document.setParseAction(self.handle_document)
        self.namespace_url.setParseAction(self.handle_namespace_url)
        self.namespace_owl.setParseAction(self.handle_namespace_owl)
        self.namespace_pattern.setParseAction(self.handle_namespace_pattern)
        self.annotation_url.setParseAction(self.handle_annotations_url)
        self.annotation_owl.setParseAction(self.handle_annotation_owl)
        self.annotation_list.setParseAction(self.handle_annotation_list)
        self.annotation_pattern.setParseAction(self.handle_annotation_pattern)

        self.language = MatchFirst([
            self.document,
            self.namespace_url,
            self.namespace_owl,
            self.annotation_url,
            self.annotation_list,
            self.annotation_owl,
            self.annotation_pattern,
            self.namespace_pattern
        ])

        BaseParser.__init__(self, self.language)

    def handle_document(self, s, l, tokens):
        key = tokens['key']
        value = tokens['value']

        if key not in DOCUMENT_KEYS:
            raise InvalidMetadataException(key, value)

        norm_key = DOCUMENT_KEYS[key]

        if norm_key in self.document_metadata:
            log.warning('Tried to overwrite metadata: %s', key)
            return tokens

        self.document_metadata[norm_key] = value

        return tokens

    def handle_namespace_url(self, s, l, tokens):
        name = tokens['name']

        if self.namespace_is_defined(name):
            log.warning('Tried to overwrite namespace: %s', name)
            return tokens

        url = tokens['url']
        terms = self.cache_manager.get_namespace(url)

        self.namespace_dict[name] = terms
        self.namespace_url_dict[name] = url

        return tokens

    def handle_namespace_owl(self, s, l, tokens):
        name = tokens['name']

        if self.namespace_is_defined(name):
            log.warning('Tried to overwrite owl namespace: %s', name)
            return tokens

        functions = set(tokens['functions'] if 'functions' in tokens else language.belns_encodings)

        url = tokens['url']

        terms = self.cache_manager.get_namespace_owl_terms(url)

        self.namespace_dict[name] = {term: functions for term in terms}
        self.namespace_owl_dict[name] = url

        return tokens

    def handle_namespace_pattern(self, s, l, tokens):
        name = tokens['name']

        if self.namespace_is_defined(name):
            log.warning('Tried to overwrite namespace: {}'.format(name))
            return tokens

        self.namespace_re[name] = tokens['value']
        return tokens

    def handle_annotation_owl(self, s, l, tokens):
        name = tokens['name']

        if self.annotation_is_defined(name):
            log.warning('Tried to overwrite annotation: {}'.format(name))
            return tokens

        url = tokens['url']

        terms = self.cache_manager.get_annotation_owl_terms(url)

        self.annotations_dict[name] = set(terms)
        self.annotations_owl_dict[name] = url

        return tokens

    def handle_annotations_url(self, s, l, tokens):
        name = tokens['name']

        if self.annotation_is_defined(name):
            log.warning('Tried to overwrite annotation: %s', name)
            return tokens

        url = tokens['url']

        self.annotations_dict[name] = self.cache_manager.get_annotation(url)
        self.annotation_url_dict[name] = url

        return tokens

    def handle_annotation_list(self, s, l, tokens):
        name = tokens['name']

        if self.annotation_is_defined(name):
            log.warning('Tried to overwrite annotation: {}'.format(name))
            return tokens

        values = set(tokens['values'])

        self.annotations_dict[name] = values
        self.annotation_list_list.append(name)

        return tokens

    def handle_annotation_pattern(self, s, l, tokens):
        name = tokens['name']

        if self.annotation_is_defined(name):
            log.warning('Tried to overwrite annotation: {}'.format(name))
            return tokens

        self.annotations_re[name] = tokens['value']
        return tokens

    def annotation_is_defined(self, key):
        return key in self.annotations_dict or key in self.annotations_re

    def namespace_is_defined(self, key):
        return key in self.namespace_dict or key in self.namespace_re
