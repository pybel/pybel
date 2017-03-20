# -*- coding: utf-8 -*-

from pyparsing import Word

from .fragment import FragmentParser
from .fusion import FusionParser
from .gene_modification import GmodParser
from .gene_substitution import GsubParser
from .location import LocationParser
from .protein_modification import PmodParser
from .protein_substitution import PsubParser
from .truncation import TruncationParser
from .variant import VariantParser
from ..language import dna_nucleotide_labels, rna_nucleotide_labels
from ...constants import FRAGMENT_START, FRAGMENT_STOP, FRAGMENT_MISSING, FRAGMENT_DESCRIPTION, GMOD_ORDER, PMOD_ORDER
from ...constants import KIND, PMOD, NAMESPACE, NAME, GMOD, FRAGMENT, HGVS, IDENTIFIER


def canonicalize_hgvs(tokens):
    return tokens[KIND], tokens[IDENTIFIER]


def canonicalize_pmod(tokens):
    return (PMOD, (tokens[IDENTIFIER][NAMESPACE], tokens[IDENTIFIER][NAME])) + tuple(
        tokens[key] for key in PMOD_ORDER[2:] if key in tokens)


def canonicalize_gmod(tokens):
    return (GMOD, (tokens[IDENTIFIER][NAMESPACE], tokens[IDENTIFIER][NAME])) + tuple(
        tokens[key] for key in GMOD_ORDER[2:] if key in tokens)


def canonicalize_frag(tokens):
    if FRAGMENT_MISSING in tokens:
        result = FRAGMENT, '?'
    else:
        result = FRAGMENT, (tokens[FRAGMENT_START], tokens[FRAGMENT_STOP])

    if FRAGMENT_DESCRIPTION in tokens:
        return result + (tokens[FRAGMENT_DESCRIPTION],)

    return result


def canonicalize_variant(tokens):
    if tokens[KIND] == HGVS:
        return canonicalize_hgvs(tokens)
    elif tokens[KIND] == PMOD:
        return canonicalize_pmod(tokens)
    elif tokens[KIND] == GMOD:
        return canonicalize_gmod(tokens)
    # elif tokens[KIND] == FRAGMENT:
    return canonicalize_frag(tokens)


dna_nucleotide_seq = Word(''.join(dna_nucleotide_labels.keys()))
rna_nucleotide_seq = Word(''.join(rna_nucleotide_labels.keys()))
