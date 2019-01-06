# -*- coding: utf-8 -*-

"""Utilities for reading BEL Script."""

import logging
from typing import Iterable, Iterator, Tuple

from multisplitby import multi_split_by

from .constants import METADATA_LINE_RE

__all__ = [
    'split_file_to_annotations_and_definitions',
]

log = logging.getLogger(__name__)

EnumLine = Tuple[int, str]
EnumLines = Iterable[EnumLine]


def split_file_to_annotations_and_definitions(lines: Iterable[str]) -> Tuple[EnumLines, EnumLines, EnumLines]:
    """Enumerate a line iterable and splits into 3 parts."""
    enum_lines = sanitize_file_lines(lines)
    metadata, definitions, statements = multi_split_by(enum_lines, [_predicate_1, _predicate_2])
    return metadata, definitions, statements


def _predicate_1(line: EnumLine) -> bool:
    return not line[1].startswith('SET DOCUMENT')


def _predicate_2(line: EnumLine) -> bool:
    return not METADATA_LINE_RE.match(line[1])


def sanitize_file_lines(lines: Iterable[str]) -> EnumLines:
    """Enumerate a line iterator and returns the pairs of (line number, line) that are cleaned."""
    line_iterator = sanitize_file_line_iter(lines)

    for line_number, line in line_iterator:
        if line.endswith('\\'):
            log.log(4, 'Multiline quote starting on line: %d', line_number)
            line = line.strip('\\').strip()
            next_line_number, next_line = next(line_iterator)
            while next_line.endswith('\\'):
                log.log(3, 'Extending line: %s', next_line)
                line += " " + next_line.strip('\\').strip()
                next_line_number, next_line = next(line_iterator)
            line += " " + next_line.strip()
            log.log(3, 'Final line: %s', line)

        elif 1 == line.count('"'):
            log.log(4, 'PyBEL013 Missing new line escapes [line: %d]', line_number)
            next_line_number, next_line = next(line_iterator)
            next_line = next_line.strip()
            while not next_line.endswith('"'):
                log.log(3, 'Extending line: %s', next_line)
                line = '{} {}'.format(line.strip(), next_line)
                next_line_number, next_line = next(line_iterator)
                next_line = next_line.strip()
            line = '{} {}'.format(line, next_line)
            log.log(3, 'Final line: %s', line)

        comment_loc = line.rfind(' //')
        if 0 <= comment_loc:
            line = line[:comment_loc]

        yield line_number, line


def sanitize_file_line_iter(file: Iterable[str], note_char: str = ':') -> Iterator[EnumLine]:
    """Clean a line iterator by removing extra whitespace, blank lines, comment lines, and log nodes.

    :param file: An iterable over the lines in a BEL Script
    :param note_char: The character sequence denoting a special note
    :returns: An iterator over the line number and the lines that should be processed
    """
    for line_number, line in enumerate(file, start=1):
        line = line.strip()

        if not line:
            continue

        if line[0] == '#':
            if len(line) > 1 and line[1] == note_char:
                log.info('NOTE: Line %d: %s', line_number, line)
            continue

        yield line_number, line
