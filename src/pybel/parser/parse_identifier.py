from pyparsing import *

from .baseparser import BaseParser, word, quote
from .parse_exceptions import NamespaceException, NakedNamespaceException


class IdentifierParser(BaseParser):
    def __init__(self, namespace_dict=None, default_namespace=None, mapping=None):
        """Builds a namespace parser.
        :param namespace_dict: dictionary of {namespace: set of names}
        :type namespace_dict: dict
        :param default_namespace: set of valid values that can be used without a namespace
        :type default_namespace: set
        :param mapping: dictionary of {namespace: {name: (mapped_ns, mapped_name)}}
        :type mapping
        :return:
        """

        self.namespace_dict = namespace_dict
        self.default_namespace = set(default_namespace) if default_namespace is not None else None

        self.identifier_qualified = word('namespace') + Suppress(':') + (word | quote)('name')

        if self.namespace_dict is not None:
            self.identifier_qualified.setParseAction(self.handle_identifier_qualified)

        self.identifier_bare = (word | quote)('name')
        if self.default_namespace is not None:
            self.identifier_bare.setParseAction(self.handle_identifier_default)
        else:
            self.identifier_bare.setParseAction(self.handle_namespace_invalid)

        if mapping is not None:
            # TODO implement
            raise NotImplementedError('Mapping not yet implemented')

        self.language = self.identifier_qualified | self.identifier_bare

    def handle_identifier_qualified(self, s, l, tokens):
        namespace = tokens['namespace']
        if namespace not in self.namespace_dict:
            raise NamespaceException('Invalid namespace: {}'.format(namespace))

        name = tokens['name']
        if name not in self.namespace_dict[namespace]:
            raise NamespaceException('Invalid {} name: {}'.format(namespace, name))

        return tokens

    def handle_identifier_default(self, s, l, tokens):
        name = tokens['name']
        if name not in self.default_namespace:
            raise NamespaceException('Default namespace missing name: {}'.format(name))
        return tokens

    def handle_namespace_invalid(self, s, l, tokens):
        raise NakedNamespaceException('Missing valid namespace: {} {} {}'.format(s,l,tokens))

    def get_language(self):
        return self.language
