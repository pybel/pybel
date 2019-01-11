# -*- coding: utf-8 -*-

"""This module contains helper functions for reading BEL scripts."""

import logging
import re
import time
from typing import Any, Iterable, List, Mapping, Optional, Tuple

from pyparsing import ParseException
from sqlalchemy.exc import OperationalError
from tqdm import tqdm

from bel_resources import ResourceError, split_file_to_annotations_and_definitions
from ..constants import INVERSE_DOCUMENT_KEYS, REQUIRED_METADATA
from ..manager import Manager
from ..parser import BELParser, MetadataParser
from ..parser.exc import (
    BELParserWarning, BELSyntaxError, InconsistentDefinitionError, MalformedMetadataException, MissingMetadataException,
    PlaceholderAminoAcidWarning, VersionFormatWarning,
)
from ..struct.graph import BELGraph

__all__ = [
    'parse_lines',
]

log = logging.getLogger(__name__)
parse_log = logging.getLogger('pybel.parser')

METADATA_LINE_RE = re.compile(r"(SET\s+DOCUMENT|DEFINE\s+NAMESPACE|DEFINE\s+ANNOTATION)")
LOG_FMT = '%d:%d %s %s'
LOG_FMT_PATH = '%s:%d:%d %s %s'


def parse_lines(graph: BELGraph,
                lines: Iterable[str],
                manager: Optional[Manager] = None,
                allow_nested: bool = False,
                citation_clearing: bool = True,
                use_tqdm: bool = False,
                tqdm_kwargs: Optional[Mapping[str, Any]] = None,
                no_identifier_validation: bool = False,
                disallow_unqualified_translocations: bool = False,
                allow_redefinition: bool = False,
                allow_definition_failures: bool = False,
                allow_naked_names: bool = False,
                required_annotations: Optional[List[str]] = None,
                ):
    """Parse an iterable of lines into this graph.

    Delegates to :func:`parse_document`, :func:`parse_definitions`, and :func:`parse_statements`.

    :param graph: A BEL graph
    :param lines: An iterable over lines of BEL script
    :param manager: A PyBEL database manager
    :param allow_nested: If true, turns off nested statement failures
    :param citation_clearing: Should :code:`SET Citation` statements clear evidence and all annotations?
                                   Delegated to :class:`pybel.parser.ControlParser`
    :param use_tqdm: Use :mod:`tqdm` to show a progress bar?
    :param tqdm_kwargs: Keywords to pass to ``tqdm``
    :param disallow_unqualified_translocations: If true, allow translocations without TO and FROM clauses.
    :param required_annotations: Annotations that are required for all statements

    .. warning::

        These options allow concessions for parsing BEL that is either **WRONG** or **UNSCIENTIFIC**. Use them at
        risk to reproducibility and validity of your results.

    :param no_identifier_validation: If true, turns off namespace validation
    :param allow_naked_names: If true, turns off naked namespace failures
    :param allow_redefinition: If true, doesn't fail on second definition of same name or annotation
    :param allow_definition_failures: If true, allows parsing to continue if a terminology file download/parse fails
    """
    docs, definitions, statements = split_file_to_annotations_and_definitions(lines)

    if manager is None:
        manager = Manager()

    metadata_parser = MetadataParser(
        manager,
        allow_redefinition=allow_redefinition,
        skip_validation=no_identifier_validation,
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
        allow_failures=allow_definition_failures,
        use_tqdm=use_tqdm,
        tqdm_kwargs=tqdm_kwargs,
    )

    bel_parser = BELParser(
        graph=graph,
        # terminologies
        namespace_to_term=metadata_parser.namespace_to_term,
        namespace_to_pattern=metadata_parser.namespace_to_pattern,
        annotation_to_term=metadata_parser.annotation_to_term,
        annotation_to_pattern=metadata_parser.annotation_to_pattern,
        annotation_to_local=metadata_parser.annotation_to_local,
        # language settings
        allow_nested=allow_nested,
        citation_clearing=citation_clearing,
        skip_validation=no_identifier_validation,
        allow_naked_names=allow_naked_names,
        disallow_unqualified_translocations=disallow_unqualified_translocations,
        required_annotations=required_annotations,
    )

    parse_statements(
        graph,
        statements,
        bel_parser,
        use_tqdm=use_tqdm,
        tqdm_kwargs=tqdm_kwargs,
    )

    log.info('Network has %d nodes and %d edges', graph.number_of_nodes(), graph.number_of_edges())


def parse_document(graph: BELGraph,
                   enumerated_lines: Iterable[Tuple[int, str]],
                   metadata_parser: MetadataParser,
                   ) -> None:
    """Parse the lines in the document section of a BEL script."""
    parse_document_start_time = time.time()

    for line_number, line in enumerated_lines:
        try:
            metadata_parser.parseString(line, line_number=line_number)
        except VersionFormatWarning as exc:
            _log_parse_exception(graph, exc)
            graph.add_warning(exc)
        except Exception as e:
            exc = MalformedMetadataException(line_number, line, 0)
            _log_parse_exception(graph, exc)
            raise exc from e

    for required in REQUIRED_METADATA:
        required_metadatum = metadata_parser.document_metadata.get(required)
        if required_metadatum is not None:
            continue

        required_metadatum_key = INVERSE_DOCUMENT_KEYS[required]
        # This has to be insert since it needs to go on the front!
        exc = MissingMetadataException.make(required_metadatum_key)
        graph.warnings.insert(0, (None, exc, {}))
        _log_parse_exception(graph, exc)

    graph.document.update(metadata_parser.document_metadata)

    log.info('Finished parsing document section in %.02f seconds', time.time() - parse_document_start_time)


def parse_definitions(graph: BELGraph,
                      enumerated_lines: Iterable[Tuple[int, str]],
                      metadata_parser: MetadataParser,
                      allow_failures: bool = False,
                      use_tqdm: bool = False,
                      tqdm_kwargs: Optional[Mapping[str, Any]] = None,
                      ) -> None:
    """Parse the lines in the definitions section of a BEL script.

    :param graph: A BEL graph
    :param enumerated_lines: An enumerated iterable over the lines in the definitions section of a BEL script
    :param metadata_parser: A metadata parser
    :param allow_failures: If true, allows parser to continue past strange failures
    :param use_tqdm: Use :mod:`tqdm` to show a progress bar?
    :param tqdm_kwargs: Keywords to pass to ``tqdm``
    :raises: pybel.parser.parse_exceptions.InconsistentDefinitionError
    :raises: pybel.resources.exc.ResourceError
    :raises: sqlalchemy.exc.OperationalError
    """
    parse_definitions_start_time = time.time()

    if use_tqdm:
        _tqdm_kwargs = dict(desc='Definitions', leave=False)
        if tqdm_kwargs:
            _tqdm_kwargs.update(tqdm_kwargs)
        enumerated_lines = tqdm(list(enumerated_lines), **_tqdm_kwargs)

    for line_number, line in enumerated_lines:
        try:
            metadata_parser.parseString(line, line_number=line_number)
        except (InconsistentDefinitionError, ResourceError) as e:
            parse_log.exception(LOG_FMT, line_number, 0, e.__class__.__name__, line)
            raise e
        except OperationalError as e:
            parse_log.warning('Need to upgrade database. See '
                              'http://pybel.readthedocs.io/en/latest/installation.html#upgrading')
            raise e
        except Exception as e:
            if not allow_failures:
                exc = MalformedMetadataException(line_number, line, 0)
                _log_parse_exception(graph, exc)
                raise exc from e

    graph.namespace_url.update(metadata_parser.namespace_url_dict)
    graph.namespace_pattern.update({
        keyword: pattern.pattern
        for keyword, pattern in metadata_parser.namespace_to_pattern.items()
    })

    graph.annotation_url.update(metadata_parser.annotation_url_dict)
    graph.annotation_pattern.update({
        keyword: pattern.pattern
        for keyword, pattern in metadata_parser.annotation_to_pattern.items()
    })
    graph.annotation_list.update(metadata_parser.annotation_to_local)
    graph.uncached_namespaces.update(metadata_parser.uncachable_namespaces)

    log.info('Finished parsing definitions section in %.02f seconds', time.time() - parse_definitions_start_time)


def parse_statements(graph: BELGraph,
                     enumerated_lines: Iterable[Tuple[int, str]],
                     bel_parser: BELParser,
                     use_tqdm: bool = False,
                     tqdm_kwargs: Optional[Mapping[str, Any]] = None,
                     ) -> None:
    """Parse a list of statements from a BEL Script.

    :param graph: A BEL graph
    :param enumerated_lines: An enumerated iterable over the lines in the statements section of a BEL script
    :param bel_parser: A BEL parser
    :param use_tqdm: Use :mod:`tqdm` to show a progress bar? Requires reading whole file to memory.
    :param tqdm_kwargs: Keywords to pass to ``tqdm``
    """
    parse_statements_start_time = time.time()

    if use_tqdm:
        _tqdm_kwargs = dict(desc='Statements')
        if tqdm_kwargs:
            _tqdm_kwargs.update(tqdm_kwargs)
        enumerated_lines = tqdm(list(enumerated_lines), **_tqdm_kwargs)

    for line_number, line in enumerated_lines:
        try:
            bel_parser.parseString(line, line_number=line_number)
        except ParseException as e:
            exc = BELSyntaxError(line_number, line, e.loc)
            _log_parse_exception(graph, exc)
            graph.add_warning(exc, bel_parser.get_annotations())
        except PlaceholderAminoAcidWarning as exc:
            exc.line_number = line_number
            _log_parse_exception(graph, exc)
            graph.add_warning(exc, bel_parser.get_annotations())
        except BELParserWarning as exc:
            _log_parse_exception(graph, exc)
            graph.add_warning(exc, bel_parser.get_annotations())
        except Exception:
            parse_log.exception(LOG_FMT, line_number, 0, 'General Failure', line)
            raise

    log.info('Parsed statements section in %.02f seconds with %d warnings', time.time() - parse_statements_start_time,
             len(graph.warnings))


def _log_parse_exception(graph: BELGraph, exc: BELParserWarning):
    if graph.path:
        parse_log.error(LOG_FMT_PATH, graph.path, exc.line_number, exc.position, exc.__class__.__name__, exc)
    else:
        parse_log.error(LOG_FMT, exc.line_number, exc.position, exc.__class__.__name__, exc)
