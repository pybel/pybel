# -*- coding: utf-8 -*-

import itertools as itt
import logging
import re

from pyparsing import (
    And, Group, Suppress, White, Word, ZeroOrMore, alphanums, dblQuotedString, delimitedList, oneOf,
    removeQuotes, replaceWith,
)

from ..constants import OBJECT, RELATION, SUBJECT
from ..utils import subdict_matches

log = logging.getLogger('pybel')

re_match_bel_header = re.compile("(SET\s+DOCUMENT|DEFINE\s+NAMESPACE|DEFINE\s+ANNOTATION)")


def any_subdict_matches(dict_of_dicts, query_dict):
    """Checks if dictionary target_dict matches one of the subdictionaries of a

    :param dict[any,dict] dict_of_dicts: dictionary of dictionaries
    :param dict query_dict: dictionary
    :return: if dictionary target_dict matches one of the subdictionaries of a
    :rtype: bool
    """
    return any(
        subdict_matches(sub_dict, query_dict)
        for sub_dict in dict_of_dicts.values()
    )


def cartesian_dictionary(d):
    """takes a dictionary of sets and provides subdicts

    :param d: a dictionary of sets
    :type d: dict[any,set[any]]
    :rtype: list

    >>> cartesian_dictionary({'A': {'1', '2'}, 'B': {'x', 'y'}})
    [{'A': '1', 'B': 'x'}, {'A': '1', 'B': 'y'}, {'A': '2', 'B': 'x'}, {'A': '2', 'B': 'y'}]
    """
    q = [
        {
            (key, value)
            for value in values
        }
        for key, values in d.items()
    ]

    return [
        dict(values)
        for values in itt.product(*q)
    ]


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
delimited_quoted_list = And([Suppress('{'), delimitedList(quote), Suppress('}')])
delimited_unquoted_list = And([Suppress('{'), delimitedList(identifier), Suppress('}')])


def nest(*content):
    """Defines a delimited list by enumerating each element of the list"""
    if len(content) == 0:
        raise ValueError('no arguments supplied')
    return And([LPF, content[0]] + list(itt.chain.from_iterable(zip(itt.repeat(C), content[1:]))) + [RPF])


def one_of_tags(tags, canonical_tag, name=None):
    """This is a convenience method for defining the tags usable in the :class:`BelParser`. For example,
    statements like g(HGNC:SNCA) can be expressed also as geneAbundance(HGNC:SNCA). The language
    must define multiple different tags that get normalized to the same thing.

    :param list[str] tags: a list of strings that are the tags for a function. For example, ['g', 'geneAbundance'] for the
                    abundance of a gene
    :param str canonical_tag: the preferred tag name. Does not have to be one of the tags. For example, 'GeneAbundance'
                            (note capitalization) is used for the abundance of a gene
    :param str name: this is the key under which the value for this tag is put in the PyParsing framework.
    :rtype: :class:`pyparsing.ParseElement`
    """
    element = oneOf(tags).setParseAction(replaceWith(canonical_tag))

    if name is None:
        return element

    return element.setResultsName(name)


def triple(subject, relation, obj):
    """Builds a simple triple in PyParsing that has a ``subject relation object`` format"""
    return And([Group(subject)(SUBJECT), relation(RELATION), Group(obj)(OBJECT)])
