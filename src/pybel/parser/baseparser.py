# -*- coding: utf-8 -*-

import itertools as itt
import logging
import time

from pyparsing import Suppress, ZeroOrMore, oneOf, White, dblQuotedString, removeQuotes, Word, alphanums, \
    delimitedList, replaceWith, Group, And

from ..constants import SUBJECT, RELATION, OBJECT

log = logging.getLogger(__name__)

W = Suppress(ZeroOrMore(White()))
C = Suppress(',')
WCW = W + C + W
LP = Suppress('(') + W
RP = W + Suppress(')')
LPF, RPF = map(Suppress, '()')

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
    return And([Group(subject)(SUBJECT), relation(RELATION), Group(obj)(OBJECT)])


class BaseParser:
    """This abstract class represents a language backed by a PyParsing statement

    Multiple parsers can be easily chained together when they are all inheriting from this base class
    """

    def __init__(self, language, streamline=False):
        self.language = language

        if streamline:
            self.streamline()

    def parse_lines(self, l):
        """Parses multiple lines successively"""
        return [self.parseString(line) for line in l]

    def parseString(self, s):
        """Parses a string with the language represented by this parser
        :param s: input string
        :type s: str
        """
        return self.language.parseString(s)

    def streamline(self):
        t = time.time()
        self.language.streamline()
        log.info('Finished streamlining %s in %.02fs', self.__class__.__name__, time.time() - t)
