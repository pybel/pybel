# -*- coding: utf-8 -*-

"""This module contains helper functions for reading BEL scripts."""

import logging
import re
import time

import six
from pyparsing import ParseException
from sqlalchemy.exc import OperationalError
from tqdm import tqdm

from ..constants import GRAPH_METADATA, INVERSE_DOCUMENT_KEYS, REQUIRED_METADATA
from ..exceptions import PyBelWarning
from ..manager import Manager
from ..parser import BelParser, MetadataParser
from ..parser.exc import (
    BelSyntaxError, InconsistentDefinitionError, MalformedMetadataException, MissingMetadataException,
    VersionFormatWarning,
)
from ..resources.document import split_file_to_annotations_and_definitions
from ..resources.exc import ResourceError

log = logging.getLogger(__name__)
parse_log = logging.getLogger('pybel.parser')

METADATA_LINE_RE = re.compile("(SET\s+DOCUMENT|DEFINE\s+NAMESPACE|DEFINE\s+ANNOTATION)")


def parse_lines(graph, lines, manager=None, allow_nested=False, citation_clearing=True, use_tqdm=False, **kwargs):
    """Parse an iterable of lines into this graph.

    Delegates to :func:`parse_document`, :func:`parse_definitions`, and :func:`parse_statements`.

    :param BELGraph graph: A BEL graph
    :param iter[str] lines: An iterable over lines of BEL script
    :type manager: Optional[Manager]
    :param bool allow_nested: If true, turns off nested statement failures
    :param bool citation_clearing: Should :code:`SET Citation` statements clear evidence and all annotations?
                                   Delegated to :class:`pybel.parser.ControlParser`
    :param bool use_tqdm: Use :mod:`tqdm` to show a progress bar?

    .. warning::

        These options allow concessions for parsing BEL that is either **WRONG** or **UNSCIENTIFIC**. Use them at
        risk to reproducibility and validity of your results.

    :param bool allow_naked_names: If true, turns off naked namespace failures
    :param bool allow_unqualified_translocations: If true, allow translocations without TO and FROM clauses.
    :param bool no_identifier_validation: If true, turns off namespace validation
    :param Optional[list[str]] required_annotations: Annotations that are required for all statements
    """
    docs, definitions, statements = split_file_to_annotations_and_definitions(lines)

    if manager is None:
        manager = Manager()

    metadata_parser = MetadataParser(
        manager,
        allow_redefinition=kwargs.get('allow_redefinition'),
    )

    parse_document(
        graph,
        docs,
        metadata_parser,
    )

    parse_definitions(
        graph,
        definitions,
        metadata_parser,
        allow_failures=kwargs.get('allow_definition_failures'),
        use_tqdm=use_tqdm,
    )

    bel_parser = BelParser(
        graph=graph,
        namespace_dict=metadata_parser.namespace_dict,
        annotation_dict=metadata_parser.annotation_dict,
        namespace_regex=metadata_parser.namespace_regex,
        annotation_regex=metadata_parser.annotation_regex,
        allow_nested=allow_nested,
        citation_clearing=citation_clearing,
        allow_naked_names=kwargs.get('allow_naked_names'),
        allow_unqualified_translocations=kwargs.get('allow_unqualified_translocations'),
        no_identifier_validation=kwargs.get('no_identifier_validation'),
        required_annotations=kwargs.get('required_annotations'),
    )

    parse_statements(
        graph,
        statements,
        bel_parser,
        use_tqdm=use_tqdm,
    )

    log.info('Network has %d nodes and %d edges', graph.number_of_nodes(), graph.number_of_edges())


def parse_document(graph, document_metadata, metadata_parser):
    """Parse the lines in the document section of a BEL script.

    :param BELGraph graph: A BEL graph
    :param iter[str] document_metadata: An enumerated iterable over the lines in the document section of a BEL script
    :param MetadataParser metadata_parser: A metadata parser
    """
    parse_document_start_time = time.time()

    for line_number, line in document_metadata:
        try:
            metadata_parser.parseString(line, line_number=line_number)
        except VersionFormatWarning as e:
            parse_log.warning('Line %07d - %s: %s', line_number, e.__class__.__name__, e)
            graph.add_warning(line_number, line, e)
        except Exception as e:
            parse_log.exception('Line %07d - Critical Failure - %s', line_number, line)
            six.raise_from(MalformedMetadataException(line_number, line), e)

    for required in REQUIRED_METADATA:
        required_metadatum = metadata_parser.document_metadata.get(required)
        if required_metadatum is not None:
            continue

        required_metadatum_key = INVERSE_DOCUMENT_KEYS[required]
        graph.warnings.insert(0, (0, '', MissingMetadataException(required_metadatum_key), {}))
        log.error('Missing required document metadata: %s', required_metadatum_key)

    graph.graph[GRAPH_METADATA] = metadata_parser.document_metadata

    log.info('Finished parsing document section in %.02f seconds', time.time() - parse_document_start_time)


def parse_definitions(graph, definitions, metadata_parser, allow_failures=False, use_tqdm=False):
    """Parse the lines in the definitions section of a BEL script.

    :param pybel.BELGraph graph: A BEL graph
    :param list[str] definitions: An enumerated iterable over the lines in the definitions section of a BEL script
    :param MetadataParser metadata_parser: A metadata parser
    :param bool allow_failures: If true, allows parser to continue past strange failures
    :param bool use_tqdm: Use :mod:`tqdm` to show a progress bar?
    :raises: pybel.parser.parse_exceptions.InconsistentDefinitionError
    :raises: pybel.resources.exc.ResourceError
    :raises: sqlalchemy.exc.OperationalError
    """
    parse_definitions_start_time = time.time()

    if use_tqdm:
        definitions = tqdm(definitions, total=len(definitions), desc='Definitions')

    for line_number, line in definitions:
        try:
            metadata_parser.parseString(line, line_number=line_number)
        except InconsistentDefinitionError as e:
            parse_log.exception('Line %07d - Critical Failure - %s', line_number, line)
            raise e
        except ResourceError as e:
            parse_log.warning("Line %07d - Can't use resouce - %s", line_number, line)
            raise e
        except OperationalError as e:
            parse_log.warning('Need to upgrade database. See '
                              'http://pybel.readthedocs.io/en/latest/installation.html#upgrading')
            raise e
        except Exception as e:
            if not allow_failures:
                parse_log.warning('Line %07d - Critical Failure - %s', line_number, line)
                six.raise_from(MalformedMetadataException(line_number, line), e)

    graph.namespace_url.update(metadata_parser.namespace_url_dict)
    graph.namespace_pattern.update(metadata_parser.namespace_regex)

    graph.annotation_url.update(metadata_parser.annotation_url_dict)
    graph.annotation_pattern.update(metadata_parser.annotation_regex)
    graph.annotation_list.update({
        keyword: metadata_parser.annotation_dict[keyword]
        for keyword in metadata_parser.annotation_lists
    })
    graph.uncached_namespaces.update(metadata_parser.uncachable_namespaces)

    log.info('Finished parsing definitions section in %.02f seconds', time.time() - parse_definitions_start_time)


def parse_statements(graph, statements, bel_parser, use_tqdm=False):
    """Parse a list of statements from a BEL Script.

    :param BELGraph graph: A BEL graph
    :param iter[str] statements: An enumerated iterable over the lines in the statements section of a BEL script
    :param BelParser bel_parser: A BEL parser
    :param bool use_tqdm: Use :mod:`tqdm` to show a progress bar?
    """
    parse_statements_start_time = time.time()

    if use_tqdm:
        statements = tqdm(statements, desc='Statements', total=len(statements))

    for line_number, line in statements:
        try:
            bel_parser.parseString(line, line_number=line_number)
        except ParseException as e:
            parse_log.error('Line %07d - General Parser Failure: %s', line_number, line)
            graph.add_warning(line_number, line, BelSyntaxError(line_number, line, e.loc),
                              bel_parser.get_annotations())
        except PyBelWarning as e:
            parse_log.warning('Line %07d - %s: %s', line_number, e.__class__.__name__, e)
            graph.add_warning(line_number, line, e, bel_parser.get_annotations())
        except Exception as e:
            parse_log.exception('Line %07d - General Failure: %s', line_number, line)
            graph.add_warning(line_number, line, e, bel_parser.get_annotations())

    log.info('Parsed statements section in %.02f seconds with %d warnings', time.time() - parse_statements_start_time,
             len(graph.warnings))
