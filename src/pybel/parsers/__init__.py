import logging
import os
import re

from .definition_statments import handle_definitions
from .set_statements import parse_commands, group_statements, sanitize_statement_lines
from .utils import parse_list, sanitize_file_lines, subitergroup

log = logging.getLogger(__name__)

re_match_bel_header = re.compile("(SET\s+DOCUMENT|DEFINE\s+NAMESPACE|DEFINE\s+ANNOTATION)")


def split_file_to_annotations_and_definitions(file):
    content = [line.strip() for line in file]

    start_of_statements = 1 + max(i for i, l in enumerate(content) if re_match_bel_header.search(l))

    definition_lines = content[:start_of_statements]
    statement_lines = content[start_of_statements:]

    return definition_lines, statement_lines


def bel_to_json(path):
    """

    :param path:
    :return:
    """
    with open(os.path.expanduser(path)) as f:
        content = sanitize_file_lines(f)

    definition_lines, statement_lines = split_file_to_annotations_and_definitions(content)

    definition_results = handle_definitions(definition_lines)

    sanitary_statement_lines = sanitize_statement_lines(statement_lines)
    parsed_commands = parse_commands(sanitary_statement_lines)
    command_results = group_statements(parsed_commands)

    return {
        'definitions': definition_results,
        'commands': command_results
    }



# TODO: Group command results by evidence
"""
[{
    citation: ...,
    evidences: [
        {
            annotations: []
            biological_statements: []
        }
    ]
]
"""

# Alternatively, keep a running dictionary with current 'Set' variables

# TODO iterate citations/evidences, validate/canonicalize expressions, generate nodes/edges, accumulate in graph
