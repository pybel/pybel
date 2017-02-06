# -*- coding: utf-8 -*-

import logging
import time
from collections import defaultdict, Counter

import networkx as nx
from pkg_resources import get_distribution
from pyparsing import ParseException

from .constants import FUNCTION, NAMESPACE
from .exceptions import PyBelWarning
from .manager.cache import CacheManager
from .parser import language
from .parser.parse_bel import BelParser
from .parser.parse_exceptions import MissingMetadataException
from .parser.parse_metadata import MetadataParser
from .parser.utils import split_file_to_annotations_and_definitions, subdict_matches
from .utils import expand_dict

try:
    import cPickle as pickle
except ImportError:
    import pickle

__all__ = ['BELGraph']

log = logging.getLogger(__name__)

METADATA_NAME = 'name'
METADATA_VERSION = 'version'
METADATA_DESCRIPTION = 'description'
METADATA_AUTHORS = 'authors'
METADATA_CONTACT = 'contact'

REQUIRED_METADATA = [
    METADATA_NAME,
    METADATA_VERSION,
    METADATA_DESCRIPTION,
    METADATA_AUTHORS,
    METADATA_CONTACT
]

GRAPH_METADATA = 'document_metadata'
GRAPH_NAMESPACE_URL = 'namespace_url'
GRAPH_NAMESPACE_OWL = 'namespace_owl'
GRAPH_NAMESPACE_PATTERN = 'namespace_pattern'
GRAPH_ANNOTATION_URL = 'annotation_url'
GRAPH_ANNOTATION_OWL = 'annotation_owl'
GRAPH_ANNOTATION_LIST = 'annotation_list'
GRAPH_PYBEL_VERSION = 'pybel_version'


def build_metadata_parser(cache_manager):
    if isinstance(cache_manager, CacheManager):
        return MetadataParser(cache_manager)
    elif isinstance(cache_manager, str):
        return MetadataParser(CacheManager(connection=cache_manager))
    else:
        return MetadataParser(CacheManager())


class BELGraph(nx.MultiDiGraph):
    """An extension of a NetworkX MultiDiGraph to hold a BEL graph."""

    def __init__(self, lines=None, complete_origin=False, cache_manager=None, allow_naked_names=False,
                 allow_nested=False, *attrs, **kwargs):
        """Parses a BEL file from an iterable of strings. This can be a file, file-like, or list of strings.

        :param lines: iterable over lines of BEL data file
        :param cache_manager: database connection string to cache, pre-built cache manager,
                    or True to use the default
        :type cache_manager: str or pybel.manager.CacheManager
        :param log_stream: a stream to write debug logging to
        :param allow_naked_names: if true, turn off naked namespace failures
        :type allow_naked_names: bool
        :param allow_nested: if true, turn off nested statement failures
        :type allow_nested: bool
        :param \*attrs: arguments to pass to :py:meth:`networkx.MultiDiGraph`
        :param \**kwargs: keyword arguments to pass to :py:meth:`networkx.MultiDiGraph`
        """
        nx.MultiDiGraph.__init__(self, *attrs, **kwargs)

        #: Stores warnings as 4-tuples with (line number, line text, exception instance, context dictionary)
        self.warnings = []
        self.graph[GRAPH_PYBEL_VERSION] = get_distribution('pybel').version

        if lines is not None:
            self.parse_lines(
                lines,
                complete_origin=complete_origin,
                cache_manager=cache_manager,
                allow_naked_names=allow_naked_names,
                allow_nested=allow_nested
            )

    def parse_lines(self, lines, cache_manager=None, complete_origin=False,
                    allow_naked_names=False, allow_nested=False):
        """Parses an iterable of lines into this graph

        :param lines: iterable over lines of BEL data file
        :param cache_manager: database connection string to cache or pre-built namespace namspace_cache manager
        :type cache_manager: str or :class:`pybel.manager.cache.CacheManager`
        :param complete_origin: add corresponding DNA and RNA entities for all proteins
        :type complete_origin: bool
        :param allow_naked_names: if true, turn off naked namespace failures
        :type allow_naked_names: bool
        :param allow_nested: if true, turn off nested statement failures
        :type allow_nested: bool
        """

        docs, definitions, states = split_file_to_annotations_and_definitions(lines)

        metadata_parser = build_metadata_parser(cache_manager)

        self.parse_document(docs, metadata_parser)

        self.parse_definitions(definitions, metadata_parser)

        bel_parser = BelParser(
            graph=self,
            valid_namespaces=metadata_parser.namespace_dict,
            valid_annotations=metadata_parser.annotations_dict,
            namespace_re=metadata_parser.namespace_re,
            complete_origin=complete_origin,
            allow_naked_names=allow_naked_names,
            allow_nested=allow_nested,
            autostreamline=True
        )

        self.parse_statements(states, bel_parser)

        log.info('Network has %d nodes and %d edges', self.number_of_nodes(), self.number_of_edges())

        counter = defaultdict(lambda: defaultdict(int))

        for n, d in self.nodes_iter(data=True):
            counter[d[FUNCTION]][d[NAMESPACE] if NAMESPACE in d else 'DEFAULT'] += 1

        for fn, nss in sorted(counter.items()):
            log.debug(' %s: %d', fn, sum(nss.values()))
            for ns, count in sorted(nss.items()):
                log.debug('   %s: %d', ns, count)

    def parse_document(self, document_metadata, metadata_parser):
        t = time.time()

        for line_number, line in document_metadata:
            try:
                metadata_parser.parseString(line)
            except Exception as e:
                log.exception('Line %07d - Critical Failure - %s', line_number, line)
                raise e

        for required in REQUIRED_METADATA:
            if required not in metadata_parser.document_metadata:
                self.add_warning(0, '', MissingMetadataException(language.inv_document_keys[required]))
                log.error('Missing required document metadata: %s', language.inv_document_keys[required])
            elif not metadata_parser.document_metadata[required]:
                self.add_warning(0, '', MissingMetadataException(language.inv_document_keys[required]))
                log.error('Missing required document metadata not filled: %s', language.inv_document_keys[required])

        self.graph[GRAPH_METADATA] = metadata_parser.document_metadata

        log.info('Finished parsing document section in %.02f seconds', time.time() - t)

    def parse_definitions(self, definitions, metadata_parser):
        t = time.time()

        for line_number, line in definitions:
            try:
                metadata_parser.parseString(line)
            except Exception as e:
                log.exception('Line %07d - Critical Failure - %s', line_number, line)
                raise e

        self.graph[GRAPH_NAMESPACE_OWL] = metadata_parser.namespace_owl_dict.copy()
        self.graph[GRAPH_NAMESPACE_URL] = metadata_parser.namespace_url_dict.copy()
        self.graph[GRAPH_NAMESPACE_PATTERN] = metadata_parser.namespace_re.copy()
        self.graph[GRAPH_ANNOTATION_URL] = metadata_parser.annotation_url_dict.copy()
        self.graph[GRAPH_ANNOTATION_OWL] = metadata_parser.annotations_owl_dict.copy()
        self.graph[GRAPH_ANNOTATION_LIST] = {e: metadata_parser.annotations_dict[e] for e in
                                             metadata_parser.annotation_list_list}

        log.info('Finished parsing definitions section in %.02f seconds', time.time() - t)

    def parse_statements(self, statements, bel_parser):
        t = time.time()

        for line_number, line in statements:
            try:
                bel_parser.parseString(line)
            except ParseException:
                log.error('Line %07d - general parser failure: %s', line_number, line)
                self.add_warning(line_number, line, PyBelWarning('ParseException'), bel_parser.get_annotations())
            except PyBelWarning as e:
                log.warning('Line %07d - %s', line_number, e)
                self.add_warning(line_number, line, e, bel_parser.get_annotations())
            except Exception as e:
                log.exception('Line %07d - general failure: %s - %s: %s', line_number, line)
                self.add_warning(line_number, line, e, bel_parser.get_annotations())

        log.info('Parsed statements section in %.02f seconds with %d warnings', time.time() - t, len(self.warnings))

        for k, v in sorted(Counter(e.__class__.__name__ for _, _, e, _ in self.warnings).items(), reverse=True):
            log.debug('  %s: %d', k, v)

    def edges_iter(self, nbunch=None, data=False, keys=False, default=None, **kwargs):
        """Allows for filtering by checking keyword arguments are a subdictionary of each edges' data.
            See :py:meth:`networkx.MultiDiGraph.edges_iter`"""
        for u, v, k, d in nx.MultiDiGraph.edges_iter(self, nbunch=nbunch, data=True, keys=True, default=default):
            if not subdict_matches(d, kwargs):
                continue
            elif keys and data:
                yield u, v, k, d
            elif data:
                yield u, v, d
            elif keys:
                yield u, v, k
            else:
                yield u, v

    def nodes_iter(self, data=False, **kwargs):
        """Allows for filtering by checking keyword arguments are a subdictionary of each nodes' data.
            See :py:meth:`networkx.MultiDiGraph.edges_iter`"""
        for n, d in nx.MultiDiGraph.nodes_iter(self, data=True):
            if not subdict_matches(d, kwargs):
                continue
            elif data:
                yield n, d
            else:
                yield n

    @property
    def document(self):
        """A dictionary holding the metadata from the "Document" section of the BEL script. All keys are normalized
        according to :py:data:`pybel.parser.language.document_keys`

        :return: metadata derived from the BEL "Document" section
        :rtype: dict
        """
        return self.graph[GRAPH_METADATA]

    @property
    def namespace_url(self):
        """A dictionary mapping the keywords used in the creation of this graph to the URLs of the BELNS file"""
        return self.graph[GRAPH_NAMESPACE_URL]

    @property
    def namespace_owl(self):
        """A dictionary mapping the keywords used in the creation of this graph to the URLs of the OWL file"""
        return self.graph[GRAPH_NAMESPACE_OWL]

    @property
    def namespace_pattern(self):
        """A dictionary mapping the keywords used in the creation of this graph to their regex patterns"""
        return self.graph[GRAPH_NAMESPACE_PATTERN]

    @property
    def annotation_url(self):
        """A dictionary mapping the keywords used in the creation of this graph to the URLs of the BELANNO file"""
        return self.graph[GRAPH_ANNOTATION_URL]

    @property
    def annotation_owl(self):
        """A dictionary mapping the keywords to the URL of the OWL file"""
        return self.graph[GRAPH_ANNOTATION_OWL]

    @property
    def annotation_list(self):
        """A dictionary mapping the keyword of locally defined annotations to a set of their values"""
        return self.graph[GRAPH_ANNOTATION_LIST]

    @property
    def pybel_version(self):
        """Stores the version of PyBEL with which this graph was produced"""
        return self.graph[GRAPH_PYBEL_VERSION]

    def add_warning(self, line_number, line, exception, context=None):
        """Adds a warning to the internal warning log in the graph, with optional context information"""
        self.warnings.append((line_number, line, exception, {} if context is None else context))


def expand_edges(graph):
    """Returns a new graph with expanded edge data dictionaries

    :param graph: nx.MultiDiGraph
    :type graph: BELGraph
    :rtype: BELGraph
    """
    g = BELGraph()

    for node, data in graph.nodes(data=True):
        g.add_node(node, data)

    for u, v, key, data in graph.edges(data=True, keys=True):
        g.add_edge(u, v, key=key, attr_dict=expand_dict(data))

    return g
