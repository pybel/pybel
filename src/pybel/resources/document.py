# -*- coding: utf-8 -*-

import logging

from .constants import METADATA_LINE_RE

log = logging.getLogger(__name__)


def sanitize_file_line_iter(f, note_char=':'):
    """Enumerates the given lines and removes empty lines/comments

    :param iter[str] f: An iterable over strings
    :param str note_char: The character sequence denoting a special note
    :rtype: iter[tuple[int,str]]
    """
    for line_number, line in enumerate(f, start=1):
        line = line.strip()

        if not line:
            continue

        if line[0] == '#':
            if len(line) > 1 and line[1] == note_char:
                log.info('NOTE: Line %d: %s', line_number, line)
            continue

        yield line_number, line


def sanitize_file_lines(f):
    """Enumerates a line iterator and returns the pairs of (line number, line) that are cleaned

    :param iter[str] f: An iterable of strings
    :rtype: iter[tuple[int,str]]
    """
    it = sanitize_file_line_iter(f)

    for line_number, line in it:
        if line.endswith('\\'):
            log.log(4, 'Multiline quote starting on line: %d', line_number)
            line = line.strip('\\').strip()
            next_line_number, next_line = next(it)
            while next_line.endswith('\\'):
                log.log(3, 'Extending line: %s', next_line)
                line += " " + next_line.strip('\\').strip()
                next_line_number, next_line = next(it)
            line += " " + next_line.strip()
            log.log(3, 'Final line: %s', line)

        elif 1 == line.count('"'):
            log.log(4, 'PyBEL013 Missing new line escapes [line: %d]', line_number)
            next_line_number, next_line = next(it)
            next_line = next_line.strip()
            while not next_line.endswith('"'):
                log.log(3, 'Extending line: %s', next_line)
                line = '{} {}'.format(line.strip(), next_line)
                next_line_number, next_line = next(it)
                next_line = next_line.strip()
            line = '{} {}'.format(line, next_line)
            log.log(3, 'Final line: %s', line)

        comment_loc = line.rfind(' //')
        if 0 <= comment_loc:
            line = line[:comment_loc]

        yield line_number, line


def split_file_to_annotations_and_definitions(file):
    """Enumerates a line iterable and splits into 3 parts

    :param iter[str] file:
    :rtype: tuple[list[str],list[str],list[str]]
    """
    content = list(sanitize_file_lines(file))

    end_document_section_index = 1 + max(
        index
        for index, (_, line) in enumerate(content)
        if line.startswith('SET DOCUMENT')
    )

    end_definitions_section_index = 1 + max(
        index
        for index, (_, line)
        in enumerate(content)
        if METADATA_LINE_RE.match(line)
    )

    log.info('File length: %d lines', len(content))
    documents = content[:end_document_section_index]
    definitions = content[end_document_section_index:end_definitions_section_index]
    statements = content[end_definitions_section_index:]

    return documents, definitions, statements
