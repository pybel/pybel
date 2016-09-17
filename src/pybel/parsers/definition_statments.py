import logging
import re

import requests

from .utils import parse_list

log = logging.getLogger(__name__)
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
    result_dict_key = None
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

    # species = None
    # if 'species' in result_dict:
    #    species = result_dict.pop('species')

    yes_no_dict = {'no': False, 'yes': True}
    for yesNoFiled in 'processingCaseSensitiveFlag', 'processingCacheableFlag':
        if yesNoFiled in result_dict:
            old_val = result_dict[yesNoFiled]
            result_dict[yesNoFiled] = yes_no_dict[old_val.lower()]

    result_dict['payload'] = dict(values)

    return result_dict
