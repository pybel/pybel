# -*- coding: utf-8 -*-

import itertools as itt
import logging
import re

from pyparsing import Suppress, ZeroOrMore, White, Word, alphanums, dblQuotedString, removeQuotes, And, delimitedList, \
    oneOf, replaceWith, Group

from ..constants import SUBJECT, RELATION, OBJECT
from ..utils import subdict_matches

log = logging.getLogger('pybel')

re_match_bel_header = re.compile("(SET\s+DOCUMENT|DEFINE\s+NAMESPACE|DEFINE\s+ANNOTATION)")


def sanitize_file_lines(f):
    """Enumerates a line iterator and returns the pairs of (line number, line) that are cleaned"""
    it = (line.strip() for line in f)
    it = ((line_number, line) for line_number, line in enumerate(it, start=1) if line and not line.startswith('#'))

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
    """Enumerates a line iterable and splits into 3 parts"""
    content = list(sanitize_file_lines(file))

    end_document_section = 1 + max(j for j, (i, l) in enumerate(content) if l.startswith('SET DOCUMENT'))
    end_definitions_section = 1 + max(j for j, (i, l) in enumerate(content) if re_match_bel_header.match(l))

    log.info('File length: %d lines', len(content))
    documents = content[:end_document_section]
    definitions = content[end_document_section:end_definitions_section]
    statements = content[end_definitions_section:]

    return documents, definitions, statements


def check_stability(ns_dict, ns_mapping):
    """Check the stability of namespace mapping

    :param ns_dict: dict of {name: set of values}
    :param ns_mapping: dict of {name: {value: (other_name, other_value)}}
    :return: if the mapping is stable
    :rtype: Boolean
    """
    flag = True
    for ns, kv in ns_mapping.items():
        if ns not in ns_dict:
            log.warning('missing namespace %s', ns)
            flag = False
            continue
        for k, (k_ns, v_val) in kv.items():
            if k not in ns_dict[ns]:
                log.warning('missing value %s', k)
                flag = False
            if k_ns not in ns_dict:
                log.warning('missing namespace link %s', k_ns)
                flag = False
            elif v_val not in ns_dict[k_ns]:
                log.warning('missing value %s in namespace %s', v_val, k_ns)
                flag = False
    return flag


def any_subdict_matches(dict_of_dicts, query_dict):
    """Checks if dictionary target_dict matches one of the subdictionaries of a

    :param dict_of_dicts: dictionary of dictionaries
    :param query_dict: dictionary
    :return: if dictionary target_dict matches one of the subdictionaries of a
    :rtype: bool
    """
    return any(subdict_matches(sd, query_dict) for sd in dict_of_dicts.values())


def cartesian_dictionary(d):
    """takes a dictionary of sets and provides subdicts

    :param d: a dictionary of sets
    :type d: dict
    :rtype: list
    """
    q = {}
    for key in d:
        q[key] = {(key, value) for value in d[key]}

    res = []
    for values in itt.product(*q.values()):
        res.append(dict(values))

    return res


def is_int(s):
    """Determines if an object can be cast to an int

    :param s: any object
    :return: true if argument can be cast to an int:
    :rtype: bool
    """
    try:
        int(s)
        return True
    except ValueError:
        return False


W = Suppress(ZeroOrMore(White()))
C = Suppress(',')
WCW = W + C + W
LPF, RPF = map(Suppress, '()')
LP = Suppress('(') + W
RP = W + Suppress(')')

word = Word(alphanums)
quote = dblQuotedString().setParseAction(removeQuotes)
delimitedSet = And([Suppress('{'), delimitedList(quote), Suppress('}')])


def nest(*content):
    """Defines a delimited list by enumerating each element of the list"""
    if len(content) == 0:
        raise ValueError('no arguments supplied')
    return And([LPF, content[0]] + list(itt.chain.from_iterable(zip(itt.repeat(C), content[1:]))) + [RPF])


def one_of_tags(tags, canonical_tag, identifier):
    """This is a convenience method for defining the tags usable in the :class:`BelParser`. For example,
    statements like g(HGNC:SNCA) can be expressed also as geneAbundance(HGNC:SNCA). The language
    must define multiple different tags that get normalized to the same thing.

    :param tags: a list of strings that are the tags for a function. For example, ['g', 'geneAbundance'] for the
                    abundance of a gene
    :type tags: list of str
    :param canonical_tag: the preferred tag name. Does not have to be one of the tags. For example, 'GeneAbundance'
                            (note capitalization) is used for the abundance of a gene
    :type canonical_tag: str
    :param identifier: this is the key under which the value for this tag is put in the PyParsing framework.
    :return: a PyParsing :class:`ParseElement`
    :rtype: :class:`ParseElement`
    """
    return oneOf(tags).setParseAction(replaceWith(canonical_tag)).setResultsName(identifier)


def triple(subject, relation, obj):
    """Builds a simple triple in PyParsing that has a ``subject relation object`` format"""
    return And([Group(subject)(SUBJECT), relation(RELATION), Group(obj)(OBJECT)])
