import json
import logging
import os
import re

import requests

log = logging.getLogger(__name__)


def sanitize_statement_lines(statement_lines):
    """
    Group multi-lines with breaks and forgotten delimiters
    :param statement_lines:
    :return:
    """
    new_lines = []
    statement_line_iter = iter(statement_lines)
    for line in statement_line_iter:

        # Group multi-line comments with slash delimiiters
        if line.startswith('SET Evidence') and (line.endswith('/') or line.endswith('\\')):

            next_line = next(statement_line_iter)

            while next_line.endswith('/') or next_line.endswith('\\'):
                line = '{} {}'.format(line[:-1].strip(), next_line)
                next_line = next(statement_line_iter)

            line = '{} {}'.format(line[:-1].strip(), next_line)

        # Group multi-line comments with forgotten delimiters
        elif line.startswith('SET Evidence') and not line.endswith('"'):
            next_line = next(statement_line_iter)

            while not next_line.endswith('"'):
                line = '{} {}'.format(line.strip(), next_line)
                next_line = next(statement_line_iter)

            line = '{} {}'.format(line, next_line)

        new_lines.append(line)
    return new_lines


re_match_bel_header = re.compile("(SET\s+DOCUMENT|DEFINE\s+NAMESPACE|DEFINE\s+ANNOTATION)")


def split_file_to_annotations_and_definitions(file):
    content = [line.strip() for line in file]

    start_of_statements = 1 + max(i for i, l in enumerate(content) if re_match_bel_header.search(l))

    definition_lines = content[:start_of_statements]
    statement_lines = content[start_of_statements:]

    return definition_lines, statement_lines


def subitergroup(iterable, key):
    poss = (i for i, v in enumerate(iterable) if key(v))
    res = []
    last = next(poss)
    for pos in poss:
        k = iterable[last]
        z = iterable[last + 1:pos]
        last = pos
        res.append((k, z))
    res.append((iterable[last], iterable[last + 1:]))
    return res


re_parse_list = re.compile('"\s*,\s*"')


def parse_list(s):
    s = s.strip('{}')
    q = re_parse_list.split(s)
    q = [z.strip('"') for z in q]
    return q


def handle_citation(s):
    q = parse_list(s)

    if len(q) == 3:
        return dict(zip(['source', 'citation', 'id'], q))
    elif len(q) == 6:
        return dict(zip(['source', 'title', 'journal', 'date', 'authors', 'id'], q))
    else:
        raise Exception('Dont know how to parse')


def handle_evidence(s):
    return s.strip('"')


re_identify_definition = re.compile(
    '^DEFINE\s*(?P<defined_element>(NAMESPACE|ANNOTATION))\s*(?P<keyName>.+?)\s+AS\s+(?P<definition_type>(URL|LIST))\s+(?P<definition>.+)$')
"""Regular expression that is used to identify definitions of Namespaces and Annotations."""


def handle_definitions(definition_lines):
    res = {}
    for line in definition_lines:

        definition = re_identify_definition.search(line)
        if not definition:
            continue
        data = definition.groupdict()

        data['definition'] = data['definition'].strip().strip('"')

        if data['definition_type'] == 'URL':
            url = data['definition']
            data['data'] = parse_definition_url(url)
            # print(data)
        elif data['definition_type'] == 'LIST':
            data['data'] = parse_list(data.pop('definition'))
            # print(data)

        key = data.pop('keyName')
        res[key] = data

    return res


def parse_commands(sanitary_statement_lines):
    """
    Parse out commands
    :param sanitary_statement_lines:
    :return:
    """
    line_cmds = []
    for line in sanitary_statement_lines:
        if line.startswith('SET'):
            line = line.strip('SET').strip()
            line = [x.strip() for x in line.split('=', 1)]
            command, value = line

            if command == 'Evidence':
                value = handle_evidence(value)

            line_cmds.append(('S', command, value))

        elif line.startswith('UNSET'):
            line = line.strip('UNSET').strip()
            line_cmds.append(('U', line))
        else:
            line_cmds.append(('X', line))
    return line_cmds


def group_statements(parsed_commands):
    """

    :param parsed_commands:
    :return:
    """
    res = []
    for command_line, subcommand_lines in subitergroup(parsed_commands, lambda t: t[0] == 'S' and t[1] == 'Citation'):
        tag, command, value = command_line

        citation = handle_citation(value)

        res.append({
            'citation': citation,
            'notes': list(z[1:] for z in subcommand_lines)
        })

    return res


def sanitize_file_lines(f):
    content = [line.strip() for line in f]
    return [line for line in content if line and not line.startswith(('#'))]


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


definitions_syntax = {
    'Namespace': {
        'NameString': 'name',
        'Keyword': 'keyword',
        'DomainString': 'domain',
        'SpeciesString': 'species',
        'DescriptionString': 'description',
        'VersionString': 'version',
        'CreatedDateTime': 'createdDateTime',
        'QueryValueURL': 'queryValueUrl',
        'UsageString': 'usageDescription',
        'TypeString': 'typeClass'
    },
    'Author': {
        'NameString': 'authorName',
        'CopyrightString': 'authorCopyright',
        'ContactInfoString': 'authorContactInfo'
    },
    'Citation': {
        'NameString': 'citationName',
        'DescriptionString': 'citationDescription',
        'PublishedVersionString': 'citationPublishedVersion',
        'PublishedDate': 'citationPublishedDate',
        'ReferenceURL': 'citationReferenceURL'
    },
    'Processing': {
        'CaseSensitiveFlag': 'processingCaseSensitiveFlag',
        'DelimiterString': 'processingDelimiter',
        'CacheableFlag': 'processingCacheableFlag'
    },
    'Values': None
}
definitions_syntax['AnnotationDefinition'] = definitions_syntax['Namespace']
"""Dictionary that contains the structure of a definition-file for Namespaces or Annotations."""


def parse_definition_url(url):
    log.info("Downloading {}".format(url))
    response = requests.get(url)
    lines = response.iter_lines()

    keyword_match = re.compile('^\[([^]]+)\]$')

    result_dict = {}
    keyword = None
    values = []
    attribute = None

    for line in lines:
        line = line.decode('utf-8').strip()

        if not line or line.startswith('#'):
            continue

        found_keyword = keyword_match.search(line)
        if found_keyword:
            if found_keyword.group(1) in definitions_syntax:
                keyword = found_keyword.group(1)
                # print('Keyword: {}'.format(keyword))
            else:
                logging.warning("Unknown keyword %s in %s" % (found_keyword.group(1), url))
        elif keyword == "Values":
            v_add = line.rsplit(result_dict['processingDelimiter'], 1)
            # print(keyword, line, v_add)
            values.append(v_add)
        else:
            regex = "^(" + "|".join(definitions_syntax[keyword].keys()) + ") *=(.*)$"
            found_attribute = re.search(regex, line)
            if found_attribute:
                attribute = found_attribute.group(1)  # Attribute name in file
                result_dict_key = definitions_syntax[keyword][attribute]  # column name in database
                result_dict[result_dict_key] = found_attribute.group(2)
            elif keyword and attribute:
                result_dict[result_dict_key] += line

    species = None
    if 'species' in result_dict:
        species = result_dict.pop('species')

    yes_no_dict = {'no': False, 'yes': True}
    for yesNoFiled in 'processingCaseSensitiveFlag', 'processingCacheableFlag':
        if yesNoFiled in result_dict:
            old_val = result_dict[yesNoFiled]
            result_dict[yesNoFiled] = yes_no_dict[old_val.lower()]

    result_dict['payload'] = dict(values)

    return result_dict
