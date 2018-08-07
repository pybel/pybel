# -*- coding: utf-8 -*-

"""Parsers for modifications to abundances."""

from .fragment import get_fragment_language
from .fusion import get_fusion_language, get_legacy_fusion_langauge
from .gene_modification import get_gene_modification_language
from .gene_substitution import get_gene_substitution_language
from .location import get_location_language
from .protein_modification import get_protein_modification_language
from .protein_substitution import get_protein_substitution_language
from .truncation import get_truncation_language
from .variant import get_hgvs_language
