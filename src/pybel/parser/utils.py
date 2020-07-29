# -*- coding: utf-8 -*-

"""Utilities for the parsers."""

import itertools as itt
import logging
from typing import Any, List, Optional

from pyparsing import (
    And, Group, ParserElement, Suppress, White, Word, ZeroOrMore, alphanums, dblQuotedString, delimitedList, oneOf,
    removeQuotes, replaceWith,
)

from ..constants import RELATION, SOURCE, TARGET

logger = logging.getLogger('pybel')


def is_int(s: Any) -> bool:
    """Determine if an object can be cast to an int.

    :param s: any object
    :return: true if argument can be cast to an int:
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
ns = Word(alphanums + '_-.')
identifier = Word(alphanums + '_')
quote = dblQuotedString().setParseAction(removeQuotes)
qid = quote | identifier
delimited_quoted_list = And([Suppress('{'), delimitedList(quote), Suppress('}')])
delimited_unquoted_list = And([Suppress('{'), delimitedList(identifier), Suppress('}')])


def nest(*content):
    """Define a delimited list by enumerating each element of the list."""
    if len(content) == 0:
        raise ValueError('no arguments supplied')
    return And([LPF, content[0]] + list(itt.chain.from_iterable(zip(itt.repeat(C), content[1:]))) + [RPF])


def one_of_tags(
    tags: List[str],
    canonical_tag: str,
    name: Optional[str] = None,
) -> ParserElement:
    """Define the tags usable in the :class:`BelParser`.

    For example, statements like ``g(HGNC:SNCA)`` can be expressed also as ``geneAbundance(HGNC:SNCA)``. The language
    must define multiple different tags that get normalized to the same thing.

    :param tags: a list of strings that are the tags for a function. For example, ['g', 'geneAbundance'] for the
                    abundance of a gene
    :param canonical_tag: the preferred tag name. Does not have to be one of the tags. For example, 'GeneAbundance'
                            (note capitalization) is used for the abundance of a gene
    :param name: this is the key under which the value for this tag is put in the PyParsing framework.
    """
    element = oneOf(tags).setParseAction(replaceWith(canonical_tag))

    if name is None:
        return element

    return element.setResultsName(name)


def triple(subject, relation, obj) -> ParserElement:
    """Build a simple triple in PyParsing that has a ``subject relation object`` format."""
    return And([Group(subject)(SOURCE), relation(RELATION), Group(obj)(TARGET)])
