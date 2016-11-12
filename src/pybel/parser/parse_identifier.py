# -*- coding: utf-8 -*-

import logging

from pyparsing import *

from .baseparser import BaseParser, word, quote
from .parse_exceptions import IllegalNamespaceException, NakedNamespaceException, IllegalNamespaceNameException, \
    IllegalDefaultNameException

log = logging.getLogger('pybel')
DIRTY = 'dirty'


class IdentifierParser(BaseParser):
    def __init__(self, valid_namespaces=None, default_namespace=None, mapping=None, lenient=False):
        """Builds a namespace parser.
        :param valid_namespaces: dictionary of {namespace: set of names}
        :type valid_namespaces: dict
        :param default_namespace: set of valid values that can be used without a namespace
        :type default_namespace: set
        :param mapping: dictionary of {namespace: {name: (mapped_ns, mapped_name)}}
        :type mapping
        :param lenient: if true, turn off naked namespace failures
        :type lenient: bool
        :return:
        """

        self.namespace_dict = valid_namespaces
        self.default_namespace = set(default_namespace) if default_namespace is not None else None

        self.identifier_qualified = word('namespace') + Suppress(':') + (word | quote)('name')

        if self.namespace_dict is not None:
            self.identifier_qualified.setParseAction(self.handle_identifier_qualified)

        self.identifier_bare = (word | quote)('name')
        if self.default_namespace is not None:
            self.identifier_bare.setParseAction(self.handle_identifier_default)
        elif lenient:
            self.identifier_bare.setParseAction(self.handle_namespace_lenient)
        else:
            self.identifier_bare.setParseAction(self.handle_namespace_invalid)

        if mapping is not None:
            # TODO implement
            raise NotImplementedError('Mapping not yet implemented')

        self.language = self.identifier_qualified | self.identifier_bare

    def handle_identifier_qualified(self, s, l, tokens):
        namespace = tokens['namespace']
        if namespace not in self.namespace_dict:
            raise IllegalNamespaceException('Invalid namespace: {}'.format(namespace))

        name = tokens['name']
        if name not in self.namespace_dict[namespace]:
            raise IllegalNamespaceNameException('Invalid {} name: {}'.format(namespace, name))

        return tokens

    def handle_identifier_default(self, s, l, tokens):
        name = tokens['name']
        if name not in self.default_namespace:
            raise IllegalDefaultNameException('Default namespace missing name: {}'.format(name))
        return tokens

    def handle_namespace_lenient(self, s, l, tokens):
        tokens['namespace'] = DIRTY
        log.debug('Naked namespace: %s', s)
        return tokens

    def handle_namespace_invalid(self, s, l, tokens):
        raise NakedNamespaceException('Missing valid namespace: {} {} {}'.format(s, l, tokens))

    def get_language(self):
        return self.language
