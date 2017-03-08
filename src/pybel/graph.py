# -*- coding: utf-8 -*-

"""

PyBEL's main data structure is a subclass of NetworkX MultiDiGraph.

The graph contains metadata for the PyBEL version, the BEL script metadata, the namespace definitions, the
annotation definitions, and the warnings produced in analysis. Like any :code:`networkx` graph, all attributes of
a given object can be accessed through the :code:`graph` property, like in: :code:`my_graph.graph['my key']`.
Convenient property definitions are given for these attributes.

"""

import itertools as itt
import logging
import time
from collections import defaultdict, Counter

import networkx as nx
from pkg_resources import get_distribution
from pyparsing import ParseException

from .constants import *
from .constructors import build_metadata_parser
from .exceptions import PyBelWarning
from .parser.parse_bel import BelParser
from .parser.parse_exceptions import MissingMetadataException
from .parser.utils import split_file_to_annotations_and_definitions, subdict_matches
from .utils import expand_dict

try:
    import cPickle as pickle
except ImportError:
    import pickle

__all__ = ['BELGraph']

log = logging.getLogger(__name__)


class BELGraph(nx.MultiDiGraph):
    """The BELGraph class is a container for BEL networks that is based on the NetworkX MultiDiGraph data structure"""

    def __init__(self, lines=None, manager=None, complete_origin=False, allow_naked_names=False,
                 allow_nested=False, citation_clearing=True, *attrs, **kwargs):
        """The default constructor parses a BEL file from an iterable of strings. This can be a file, file-like, or
        list of strings.

        :param lines: iterable over lines of BEL script
        :param manager: database connection string to cache, pre-built CacheManager, pre-built MetadataParser
                        or None to use default cache
        :type manager: str or pybel.manager.CacheManager or pybel.parser.MetadataParser
        :param complete_origin: add corresponding DNA and RNA entities for all proteins
        :type complete_origin: bool
        :param allow_naked_names: if true, turn off naked namespace failures
        :type allow_naked_names: bool
        :param allow_nested: if true, turn off nested statement failures
        :type allow_nested: bool
        :param citation_clearing: Should :code:`SET Citation` statements clear evidence and all annotations?
                                    Delegated to :class:`pybel.parser.ControlParser`
        :type citation_clearing: bool
        :param \*attrs: arguments to pass to :py:meth:`networkx.MultiDiGraph`
        :param \**kwargs: keyword arguments to pass to :py:meth:`networkx.MultiDiGraph`
        """
        nx.MultiDiGraph.__init__(self, *attrs, **kwargs)

        self._warnings = []
        self.graph[GRAPH_PYBEL_VERSION] = get_distribution('pybel').version

        if lines is not None:
            self.parse_lines(
                lines,
                manager=manager,
                complete_origin=complete_origin,
                allow_naked_names=allow_naked_names,
                allow_nested=allow_nested,
                citation_clearing=citation_clearing
            )

    def parse_lines(self, lines, manager=None, complete_origin=False, allow_naked_names=False, allow_nested=False,
                    citation_clearing=True):
        """Parses an iterable of lines into this graph

        :param lines: iterable over lines of BEL data file
        :param manager: database connection string to cache, pre-built CacheManager, or pre-build MetadataParser, or
                        None for default connection
        :type manager: None or str or :class:`pybel.manager.cache.CacheManager` or :class:`pybel.parser.MetadataParser`
        :param complete_origin: add corresponding DNA and RNA entities for all proteins
        :type complete_origin: bool
        :param allow_naked_names: if true, turn off naked namespace failures
        :type allow_naked_names: bool
        :param allow_nested: if true, turn off nested statement failures
        :type allow_nested: bool
        :param citation_clearing: Should :code:`SET Citation` statements clear evidence and all annotations?
                                    Delegated to :class:`pybel.parser.ControlParser`
        :type citation_clearing: bool
        """

        docs, definitions, states = split_file_to_annotations_and_definitions(lines)

        metadata_parser = build_metadata_parser(manager)

        self.parse_document(docs, metadata_parser)

        self.parse_definitions(definitions, metadata_parser)

        bel_parser = BelParser(
            graph=self,
            namespace_dicts=metadata_parser.namespace_dict,
            annotation_dicts=metadata_parser.annotations_dict,
            namespace_expressions=metadata_parser.namespace_re,
            annotation_expressions=metadata_parser.annotations_re,
            complete_origin=complete_origin,
            allow_naked_names=allow_naked_names,
            allow_nested=allow_nested,
            citation_clearing=citation_clearing,
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
                self.add_warning(0, '', MissingMetadataException(INVERSE_DOCUMENT_KEYS[required]))
                log.error('Missing required document metadata: %s', INVERSE_DOCUMENT_KEYS[required])
            elif not metadata_parser.document_metadata[required]:
                self.add_warning(0, '', MissingMetadataException(INVERSE_DOCUMENT_KEYS[required]))
                log.error('Missing required document metadata not filled: %s', INVERSE_DOCUMENT_KEYS[required])

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

        self.graph.update({
            GRAPH_NAMESPACE_OWL: metadata_parser.namespace_owl_dict.copy(),
            GRAPH_NAMESPACE_URL: metadata_parser.namespace_url_dict.copy(),
            GRAPH_NAMESPACE_PATTERN: metadata_parser.namespace_re.copy(),
            GRAPH_ANNOTATION_URL: metadata_parser.annotation_url_dict.copy(),
            GRAPH_ANNOTATION_OWL: metadata_parser.annotations_owl_dict.copy(),
            GRAPH_ANNOTATION_PATTERN: metadata_parser.annotations_re.copy(),
            GRAPH_ANNOTATION_LIST: {e: metadata_parser.annotations_dict[e] for e in
                                    metadata_parser.annotation_list_list}
        })

        log.info('Finished parsing definitions section in %.02f seconds', time.time() - t)

    def add_unqualified_edge(self, u, v, relation):
        """Adds unique edge that has no annotations

        :param u: source node
        :type u: tuple
        :param v: target node
        :type v: tuple
        :param relation: relationship label from :code:`pybel.constants`
        :type relation: str
        """
        key = unqualified_edge_code[relation]
        if not self.has_edge(u, v, key):
            self.add_edge(u, v, key=key, **{RELATION: relation, ANNOTATIONS: {}})

    def parse_statements(self, statements, bel_parser):
        """Parses a list of statements from a BEL Script

        :type statements: list of str
        :type bel_parser: BelParser
        """
        t = time.time()

        for line_number, line in statements:
            try:
                bel_parser.parseString(line)
            except ParseException:
                log.error('Line %07d - General Parser Failure: %s', line_number, line)
                self.add_warning(line_number, line, PyBelWarning('ParseException'), bel_parser.get_annotations())
            except PyBelWarning as e:
                log.warning('Line %07d - %s: %s', line_number, e.__class__.__name__, e)
                self.add_warning(line_number, line, e, bel_parser.get_annotations())
            except Exception as e:
                log.exception('Line %07d - General Failure: %s', line_number, line)
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

    def add_simple_node(self, function, namespace, name):
        """Adds a simple node, with only a namespace and name

        :param function: The node's function (GENE, RNA, PROTEIN, etc)
        :type function: str
        :param namespace: The namespace
        :type namespace: str
        :param name: The name of the node
        :type name: str
        """
        node = function, namespace, name
        if node not in self:
            self.add_node(node, **{FUNCTION: function, NAMESPACE: namespace, NAME: name})

    @property
    def document(self):
        """A dictionary holding the metadata from the "Document" section of the BEL script. All keys are normalized
        according to :py:data:`pybel.constants.DOCUMENT_KEYS`
        """
        return self.graph.get(GRAPH_METADATA, {})

    @property
    def namespace_url(self):
        """A dictionary mapping the keywords used to create this graph to the URLs of the BELNS file"""
        return self.graph.get(GRAPH_NAMESPACE_URL, {})

    @property
    def namespace_owl(self):
        """A dictionary mapping the keywords used to create this graph to the URLs of the OWL file"""
        return self.graph.get(GRAPH_NAMESPACE_OWL, {})

    @property
    def namespace_pattern(self):
        """A dictionary mapping the namespace keywords used to create this graph to their regex patterns"""
        return self.graph.get(GRAPH_NAMESPACE_PATTERN, {})

    @property
    def annotation_url(self):
        """A dictionary mapping the annotation keywords used to create this graph to the URLs of the BELANNO file"""
        return self.graph.get(GRAPH_ANNOTATION_URL, {})

    @property
    def annotation_owl(self):
        """A dictionary mapping the annotation keywords to the URL of the OWL file"""
        return self.graph.get(GRAPH_ANNOTATION_OWL, {})

    @property
    def annotation_pattern(self):
        """A dictionary mapping the annotation keywords used to create this graph to their regex patterns"""
        return self.graph.get(GRAPH_ANNOTATION_PATTERN, {})

    @property
    def annotation_list(self):
        """A dictionary mapping the keywords of locally defined annotations to a set of their values"""
        return self.graph.get(GRAPH_ANNOTATION_LIST, {})

    @property
    def pybel_version(self):
        """Stores the version of PyBEL with which this graph was produced as a string"""
        return self.graph[GRAPH_PYBEL_VERSION]

    @property
    def warnings(self):
        """Warnings are stored in a list of 4-tuples that is a property of the graph object.
        This tuple respectively contains the line number, the line text, the exception instance, and the context
        dictionary from the parser at the time of error.
        """
        return self._warnings

    def add_warning(self, line_number, line, exception, context=None):
        """Adds a warning to the internal warning log in the graph, with optional context information"""
        self.warnings.append((line_number, line, exception, {} if context is None else context))

    def __eq__(self, other):

        if not isinstance(other, BELGraph):
            return False

        if set(self.nodes_iter()) != set(other.nodes_iter()):
            return False

        if set(self.edges_iter()) != set(other.edges_iter()):
            return False

        for u, v in self.edges():
            i = itt.product(self.edge[u][v].values(), other.edge[u][v].values())
            r = list(filter(lambda q: q[0] == q[1], i))
            if len(self.edge[u][v]) != len(r):
                return False

        return True


def expand_edges(graph):
    """Returns a new graph with expanded edge data dictionaries

    :param graph: A BEL Graph
    :type graph: BELGraph
    :return: A new graph with expanded edge data dictionaries
    :rtype: BELGraph
    """
    g = BELGraph()

    for node, data in graph.nodes(data=True):
        g.add_node(node, data)

    for u, v, key, data in graph.edges(data=True, keys=True):
        g.add_edge(u, v, key=key, attr_dict=expand_dict(data))

    return g
