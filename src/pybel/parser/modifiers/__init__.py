# -*- coding: utf-8 -*-

from .fragment import FragmentParser
from .fusion import FusionParser
from .gene_modification import GeneModificationParser
from .gene_substitution import GeneSubstitutionParser
from .location import LocationParser
from .protein_modification import ProteinModificationParser
from .protein_substitution import ProteinSubstitutionParser
from .truncation import TruncationParser
from .variant import VariantParser

__all__ = [
    'FragmentParser',
    'FusionParser',
    'GeneModificationParser',
    'GeneSubstitutionParser',
    'LocationParser',
    'ProteinModificationParser',
    'ProteinSubstitutionParser',
    'TruncationParser',
    'VariantParser'
]
