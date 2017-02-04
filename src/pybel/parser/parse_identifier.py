# -*- coding: utf-8 -*-

import logging
import re

from pyparsing import *

from .baseparser import BaseParser, word, quote
from .parse_exceptions import UndefinedNamespaceWarning, NakedNameWarning, MissingNamespaceNameWarning, \
    MissingDefaultNameWarning, MissingNamespaceRegexWarning
from ..constants import DIRTY, NAMESPACE, NAME

log = logging.getLogger(__name__)


class IdentifierParser(BaseParser):
    def __init__(self, valid_namespaces=None, default_namespace=None, namespace_re=None, mapping=None,
                 allow_naked_names=False):
        """Builds a namespace parser.
        :param valid_namespaces: dictionary of {namespace: set of names}
        :type valid_namespaces: dict
        :param default_namespace: set of valid values that can be used without a namespace
        :type default_namespace: set
        :param mapping: dictionary of {namespace: {name: (mapped_ns, mapped_name)}}
        :type mapping
        :param allow_naked_names: if true, turn off naked namespace failures
        :type allow_naked_names: bool
        :return:
        """

        self.namespace_dict = valid_namespaces
        self.namespace_re = {k: re.compile(v) for k, v in namespace_re.items()} if namespace_re is not None else {}
        self.default_namespace = set(default_namespace) if default_namespace is not None else None

        self.identifier_qualified = word(NAMESPACE) + Suppress(':') + (word | quote)(NAME)

        if self.namespace_dict is not None:
            self.identifier_qualified.setParseAction(self.handle_identifier_qualified)

        self.identifier_bare = (word | quote)(NAME)
        if self.default_namespace is not None:
            self.identifier_bare.setParseAction(self.handle_identifier_default)
        elif allow_naked_names:
            self.identifier_bare.setParseAction(self.handle_namespace_lenient)
        else:
            self.identifier_bare.setParseAction(self.handle_namespace_invalid)

        if mapping is not None:
            # TODO implement
            raise NotImplementedError('Mapping not yet implemented')

        self.language = self.identifier_qualified | self.identifier_bare

    def handle_identifier_qualified(self, s, l, tokens):
        namespace = tokens[NAMESPACE]

        if namespace not in self.namespace_dict and namespace not in self.namespace_re:
            raise UndefinedNamespaceWarning('"{}" is not defined as a namespace'.format(namespace))

        name = tokens[NAME]
        if namespace in self.namespace_dict and name not in self.namespace_dict[namespace]:
            raise MissingNamespaceNameWarning(name, namespace)
        elif namespace in self.namespace_re and not self.namespace_re[namespace].search(name):
            raise MissingNamespaceRegexWarning(name, namespace)

        return tokens

    def handle_identifier_default(self, s, l, tokens):
        name = tokens[NAME]
        if name not in self.default_namespace:
            raise MissingDefaultNameWarning('"{}" is not in the default namespace'.format(name))
        return tokens

    def handle_namespace_lenient(self, s, l, tokens):
        tokens[NAMESPACE] = DIRTY
        log.debug('Naked namespace: %s', s)
        return tokens

    def handle_namespace_invalid(self, s, l, tokens):
        raise NakedNameWarning(tokens[NAME])

    def get_language(self):
        return self.language
