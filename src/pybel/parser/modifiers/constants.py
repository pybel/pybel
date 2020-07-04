# -*- coding: utf-8 -*-

"""Constants for modifier parsers."""

from pyparsing import Keyword, MatchFirst, oneOf

from ... import language
from ...exceptions import PlaceholderAminoAcidWarning

aa_single = oneOf(list(language.amino_acid_dict.keys()))
aa_single.setParseAction(lambda s, l, t: [language.amino_acid_dict[t[0]]])

aa_triple = oneOf(list(language.amino_acid_dict.values()))

#: In biological literature, the X is used to denote a truncation. Text mining efforts often encode X as an amino
#: acid, for which we will throw an error using :func:`handle_aa_placeholder`
aa_placeholder = Keyword('X')


def handle_aa_placeholder(line, position, tokens):
    """Raise an exception when encountering a placeholder amino acid, ``X``."""
    raise PlaceholderAminoAcidWarning(-1, line, position, tokens[0])


aa_placeholder.setParseAction(handle_aa_placeholder)

amino_acid = MatchFirst([aa_triple, aa_single, aa_placeholder])
