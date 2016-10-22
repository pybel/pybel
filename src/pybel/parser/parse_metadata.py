import logging

from pyparsing import Suppress
from pyparsing import pyparsing_common as ppc

from .baseparser import BaseParser, W, word, quote, delimitedSet
from ..utils import download_url

log = logging.getLogger('pybel')

__all__ = ['MetadataParser']

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

    def __init__(self, valid_namespaces=None, valid_annotations=None, ns_cache_manager=None):
        """
        :param valid_namespaces: dictionary of pre-loaded namespaces {name: set of valid values}
        :type valid_namespaces: dict
        :param valid_annotations: dictionary of pre-loaded annotations {name: set of valid values}
        :type valid_annotations: dict
        :param ns_cache_manager: a namespace cache manager
        :type ns_cache_manager: pybel.manager.NamespaceCache
        :return:
        """
        self.document_metadata = {}

        self.namespace_metadata = {}
        self.namespace_dict = {} if valid_namespaces is None else valid_namespaces

        self.annotations_metadata = {}
        self.annotations_dict = {} if valid_annotations is None else valid_annotations

        self.ns_cache_manager = ns_cache_manager

        # word_under = Word(alphanums + '_')
        word_under = ppc.identifier

        self.document = Suppress('SET') + W + Suppress('DOCUMENT') + W + word('key') + W + Suppress('=') + W + quote(
            'value')

        namespace_tag = Suppress('DEFINE') + W + Suppress('NAMESPACE')
        self.namespace_url = namespace_tag + W + word_under('name') + W + Suppress('AS') + W + Suppress(
            'URL') + W + quote(
            'url')
        self.namespace_list = namespace_tag + W + word_under('name') + W + Suppress('AS') + W + Suppress(
            'LIST') + W + delimitedSet('values')

        annotation_tag = Suppress('DEFINE') + W + Suppress('ANNOTATION')
        self.annotation_url = annotation_tag + W + word_under('name') + W + Suppress('AS') + W + Suppress(
            'URL') + W + quote(
            'url')
        self.annotation_list = annotation_tag + W + word_under('name') + W + Suppress('AS') + W + Suppress(
            'LIST') + W + delimitedSet('values')
        self.annotation_pattern = annotation_tag + W + word_under('name') + W + Suppress('AS') + W + Suppress(
            'PATTERN') + W + quote('value')

        self.document.setParseAction(self.handle_document)
        self.namespace_url.setParseAction(self.handle_namespace_url)
        self.namespace_list.setParseAction(self.handle_namespace_list)
        self.annotation_url.setParseAction(self.handle_annotations_url)
        self.annotation_list.setParseAction(self.handle_annotation_list)
        self.annotation_pattern.setParseAction(self.handle_annotation_pattern)

        self.language = (self.document | self.namespace_url | self.namespace_list |
                         self.annotation_url | self.annotation_list | self.annotation_pattern)

    def get_language(self):
        return self.language

    def handle_document(self, s, l, tokens):
        self.document_metadata[tokens['key']] = tokens['value']
        return tokens

    def handle_namespace_url(self, s, l, tokens):
        name = tokens['name']

        if name in self.namespace_dict:
            log.warning('Tried to overwrite namespace: {}'.format(name))
            return tokens

        url = tokens['url']

        if self.ns_cache_manager is not None:
            self.ns_cache_manager.update_namespace(url, remove_old_namespace=False)
            log.debug('Retrieved namespace {} from cache'.format(name))
            self.namespace_dict[name] = self.ns_cache_manager.cache[url]
            return tokens

        log.debug('Downloading namespace {} from {}'.format(name, url))
        config = download_url(url)

        config_keyword = config['Namespace']['Keyword']
        if name != config_keyword and name.lower() == config_keyword.lower():
            log.warning('Lexicography error. {} should be {}'.format(name, url))
            # raise LexicographyException('{} should be {}'.format(name, config_keyword))
        elif name != config_keyword:
            log.warning('Annotation name mismatch for {}: {}'.format(name, url))
            # raise NamespaceMismatch('Namespace name mismatch for {}: {}'.format(name, url))

        self.namespace_dict[name] = config['Values']
        self.namespace_metadata[name] = {k: v for k, v in config.items() if k != 'Values'}

        return tokens

    def handle_annotations_url(self, s, l, tokens):
        name = tokens['name']
        if name in self.annotations_dict:
            log.warning('Tried to overwrite annotation: {}'.format(name))
            return tokens

        url = tokens['url']
        log.debug('Downloading annotations {} from {}'.format(name, url))
        config = download_url(url)

        config_keyword = config['AnnotationDefinition']['Keyword']
        if name != config_keyword and name.lower() == config_keyword.lower():
            # raise LexicographyException('{} should be {}'.format(name, config_keyword))
            log.warning('Lexicography error. {} should be {}'.format(name, url))
        elif name != config_keyword:
            log.warning('Annotation name mismatch for {}: {}'.format(name, url))
            # raise AnnotationMismatch

        self.annotations_dict[name] = config['Values']
        self.annotations_metadata[name] = {k: v for k, v in config.items() if k != 'Values'}

        return tokens

    def handle_namespace_list(self, s, l, tokens):
        name = tokens['name']
        if name in self.namespace_dict:
            return tokens

        self.namespace_dict[name] = set(tokens['values'])

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
