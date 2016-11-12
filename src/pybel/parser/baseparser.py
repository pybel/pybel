# -*- coding: utf-8 -*-

import itertools as itt
import logging

from pyparsing import Suppress, ZeroOrMore, oneOf, White, dblQuotedString, removeQuotes, Word, alphanums, \
    delimitedList, replaceWith, Group, And

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
    return oneOf(tags).setParseAction(replaceWith(canonical_tag)).setResultsName(identifier)


def triple(subject, relation, obj):
    return And([Group(subject)('subject'), relation('relation'), Group(obj)('object')])


class BaseParser:
    """This abstract class represents a language backed by a PyParsing statement

    Multiple parsers can be easily chained together when they are all inheriting from this base class
    """

    def parse_lines(self, l):
        """Parses multiple lines successively"""
        return [self.parseString(line) for line in l]

    def parseString(self, s):
        """Parses a string with the language represented by this parser
        :param s: input string
        :type s: str
        """
        return self.get_language().parseString(s)

    def get_language(self):
        """Gets the language represented by this parser"""
        if not hasattr(self, 'language'):
            raise Exception('Language not defined')
        return self.language
