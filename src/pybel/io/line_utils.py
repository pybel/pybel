# -*- coding: utf-8 -*-

"""This module contains helper functions for reading BEL scripts"""

import time
from collections import defaultdict, Counter

from pyparsing import ParseException

from ..constants import FUNCTION, NAMESPACE, REQUIRED_METADATA, INVERSE_DOCUMENT_KEYS, GRAPH_METADATA, \
    GRAPH_NAMESPACE_OWL, GRAPH_NAMESPACE_URL, GRAPH_NAMESPACE_PATTERN, GRAPH_ANNOTATION_URL, GRAPH_ANNOTATION_OWL, \
    GRAPH_ANNOTATION_PATTERN, GRAPH_ANNOTATION_LIST
from ..exceptions import PyBelWarning
from ..graph import log
from ..manager.cache import CacheManager
from ..parser import BelParser
from ..parser import MetadataParser
from ..parser.parse_exceptions import NotSemanticVersionException, MissingMetadataException
from ..parser.utils import split_file_to_annotations_and_definitions


def parse_lines(graph, lines, manager=None, allow_naked_names=False, allow_nested=False, citation_clearing=True):
    """Parses an iterable of lines into this graph. Delegates to :func:`parse_document`, :func:`parse_definitions`, 
    and :func:`parse_statements`.

    :param graph: A BEL graph
    :type graph: BELGraph
    :param lines: An iterable over lines of BEL script
    :param manager: A database connection string to the PyBEL cache, pre-built CacheManager, or pre-build 
                    MetadataParser, or ``None`` for default connection
    :type manager: None or str or :class:`pybel.manager.cache.CacheManager` or :class:`pybel.parser.MetadataParser`
    :param allow_naked_names: If true, turns off naked namespace failures
    :type allow_naked_names: bool
    :param allow_nested: If true, turns off nested statement failures
    :type allow_nested: bool
    :param citation_clearing: Should :code:`SET Citation` statements clear evidence and all annotations?
                                Delegated to :class:`pybel.parser.ControlParser`
    :type citation_clearing: bool
    """

    docs, definitions, statements = split_file_to_annotations_and_definitions(lines)

    metadata_parser = build_metadata_parser(manager)

    parse_document(graph, docs, metadata_parser)

    parse_definitions(graph, definitions, metadata_parser)

    bel_parser = BelParser(
        graph=graph,
        namespace_dicts=metadata_parser.namespace_dict,
        annotation_dicts=metadata_parser.annotations_dict,
        namespace_expressions=metadata_parser.namespace_regex,
        annotation_expressions=metadata_parser.annotations_regex,
        allow_naked_names=allow_naked_names,
        allow_nested=allow_nested,
        citation_clearing=citation_clearing,
    )

    parse_statements(graph, statements, bel_parser)

    log.info('Network has %d nodes and %d edges', graph.number_of_nodes(), graph.number_of_edges())

    counter = defaultdict(lambda: defaultdict(int))

    for n, d in graph.nodes_iter(data=True):
        counter[d[FUNCTION]][d[NAMESPACE] if NAMESPACE in d else 'DEFAULT'] += 1

    for fn, nss in sorted(counter.items()):
        log.debug(' %s: %d', fn, sum(nss.values()))
        for ns, count in sorted(nss.items()):
            log.debug('   %s: %d', ns, count)


def parse_document(graph, document_metadata, metadata_parser):
    """Parses the lines in the document section of a BEL script.

    :param graph: A BEL graph
    :type graph: BELGraph
    :param document_metadata: An enumerated iterable over the lines in the document section of a BEL script
    :type document_metadata: iter
    :param metadata_parser: A metadata parser
    :type metadata_parser: pybel.parser.parse_metadata.MetadataParser
    :return:
    """
    t = time.time()

    for line_number, line in document_metadata:
        try:
            metadata_parser.parseString(line)
        except NotSemanticVersionException as e:
            log.warning('Line %07d - %s: %s', line_number, e.__class__.__name__, e)
            graph.add_warning(line_number, line, e)
        except Exception as e:
            log.exception('Line %07d - Critical Failure - %s', line_number, line)
            raise e

    for required in REQUIRED_METADATA:
        if required in metadata_parser.document_metadata and metadata_parser.document_metadata[required]:
            continue
        graph.warnings.insert(0, (0, '', MissingMetadataException(INVERSE_DOCUMENT_KEYS[required]), {}))
        log.error('Missing required document metadata: %s', INVERSE_DOCUMENT_KEYS[required])

    graph.graph[GRAPH_METADATA] = metadata_parser.document_metadata

    log.info('Finished parsing document section in %.02f seconds', time.time() - t)


def parse_definitions(graph, definitions, metadata_parser):
    """Parses the lines in the definitions section of a BEL script.

    :param graph: A BEL graph
    :type graph: BELGraph
    :param definitions: An enumerated iterable over the lines in the definitions section of a BEL script
    :type definitions: iter
    :param metadata_parser: A metadata parser
    :type metadata_parser: pybel.parser.parse_metadata.MetadataParser
    :return:
    """
    t = time.time()

    for line_number, line in definitions:
        try:
            metadata_parser.parseString(line)
        except Exception as e:
            log.exception('Line %07d - Critical Failure - %s', line_number, line)
            raise e

    graph.graph.update({
        GRAPH_NAMESPACE_OWL: metadata_parser.namespace_owl_dict.copy(),
        GRAPH_NAMESPACE_URL: metadata_parser.namespace_url_dict.copy(),
        GRAPH_NAMESPACE_PATTERN: metadata_parser.namespace_regex.copy(),
        GRAPH_ANNOTATION_URL: metadata_parser.annotation_url_dict.copy(),
        GRAPH_ANNOTATION_OWL: metadata_parser.annotations_owl_dict.copy(),
        GRAPH_ANNOTATION_PATTERN: metadata_parser.annotations_regex.copy(),
        GRAPH_ANNOTATION_LIST: {e: metadata_parser.annotations_dict[e] for e in
                                metadata_parser.annotation_list_list}
    })

    log.info('Finished parsing definitions section in %.02f seconds', time.time() - t)


def parse_statements(graph, statements, bel_parser):
    """Parses a list of statements from a BEL Script.

    :param graph: A BEL graph
    :type graph: BELGraph
    :param statements: An enumerated iterable over the lines in the statements section of a BEL script
    :type statements: iter
    :param bel_parser: A BEL parser
    :type bel_parser: BelParser
    """
    t = time.time()

    for line_number, line in statements:
        try:
            bel_parser.parseString(line)
        except ParseException:
            log.error('Line %07d - General Parser Failure: %s', line_number, line)
            graph.add_warning(line_number, line, PyBelWarning('Unable to parse line'), bel_parser.get_annotations())
        except PyBelWarning as e:
            log.warning('Line %07d - %s: %s', line_number, e.__class__.__name__, e)
            graph.add_warning(line_number, line, e, bel_parser.get_annotations())
        except Exception as e:
            log.exception('Line %07d - General Failure: %s', line_number, line)
            graph.add_warning(line_number, line, e, bel_parser.get_annotations())

    graph.has_singleton_terms = bel_parser.has_singleton_terms

    log.info('Parsed statements section in %.02f seconds with %d warnings', time.time() - t, len(graph.warnings))

    for k, v in sorted(Counter(e.__class__.__name__ for _, _, e, _ in graph.warnings).items(), reverse=True):
        log.debug('  %s: %d', k, v)


def build_metadata_parser(manager=None):
    """Builds a metadata parser
    
    :param manager: 
    :type manager: None or str or CacheManager or MetadataParser
    :return: A metadata parser
    :rtype: MetadataParser
    """
    if isinstance(manager, MetadataParser):
        return manager

    elif isinstance(manager, CacheManager):
        return MetadataParser(manager)

    elif isinstance(manager, str):
        return MetadataParser(CacheManager(connection=manager))

    return MetadataParser(CacheManager())
