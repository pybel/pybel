from pyparsing import *

from .baseparser import BaseParser, word, quote


class NamespaceParser(BaseParser):
    def __init__(self, namespace_dict=None, default_namespace=None, mapping=None):
        """Builds a namespace parser
        :param namespace_dict:
        :type namespace_dict: dict
        :param default_namespace:
        :type default_namespace: iterable
        :return:
        """

        self.namespace_dict = namespace_dict
        self.default_namespace = set(default_namespace) if default_namespace is not None else None

        self.namespace_qualified = word('namespace') + Suppress(':') + (word | quote)('value')

        if self.namespace_dict is not None:
            self.namespace_qualified.setParseAction(self.handle_namespace_qualified)

        self.namespace_bare = (word | quote)('value')
        if default_namespace is not None:
            self.namespace_bare.setParseAction(self.handle_namespace_default)
        else:
            self.namespace_bare.setParseAction(self.handle_namespace_invalid)

        if mapping is not None:
            raise NotImplementedError('Mapping not yet implemented')

        self.language = self.namespace_qualified | self.namespace_bare

    def handle_namespace_qualified(self, s, l, tokens):
        namespace = tokens['namespace']
        if namespace not in self.namespace_dict:
            raise Exception('Invalid namespace: {}'.format(namespace))

        value = tokens['value']
        if value not in self.namespace_dict[namespace]:
            raise Exception('Invalid {} value: {}'.format(namespace, value))

        return tokens

    def handle_namespace_default(self, s, l, tokens):
        value = tokens['value']
        if value not in self.default_namespace:
            raise Exception('Default namespace missing value: {}'.format(value))
        return tokens

    def handle_namespace_invalid(self, s, l, tokens):
        raise Exception('Missing valid namespace.')

    def get_language(self):
        return self.language
