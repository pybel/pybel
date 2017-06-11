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
identifier = Word(alphanums + '_')
quote = dblQuotedString().setParseAction(removeQuotes)
qid = quote | identifier
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
