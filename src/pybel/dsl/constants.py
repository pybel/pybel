# -*- coding: utf-8 -*-

"""Convenient dictionaries for mapping constants to DSL classes."""

from .node_classes import (
    Abundance, BiologicalProcess, ComplexAbundance, CompositeAbundance, Gene, GeneFusion, MicroRna, NamedComplexAbundance,
    Pathology, Protein, ProteinFusion, Rna, RnaFusion,
)
from ..constants import ABUNDANCE, BIOPROCESS, COMPLEX, COMPOSITE, GENE, MIRNA, PATHOLOGY, PROTEIN, RNA

__all__ = [
    'FUNC_TO_DSL',
    'FUNC_TO_FUSION_DSL',
    'FUNC_TO_LIST_DSL'
]

FUNC_TO_DSL = {
    PROTEIN: Protein,
    RNA: Rna,
    MIRNA: MicroRna,
    GENE: Gene,
    PATHOLOGY: Pathology,
    BIOPROCESS: BiologicalProcess,
    COMPLEX: NamedComplexAbundance,
    ABUNDANCE: Abundance,
}

FUNC_TO_FUSION_DSL = {
    GENE: GeneFusion,
    RNA: RnaFusion,
    PROTEIN: ProteinFusion,
}

FUNC_TO_LIST_DSL = {
    COMPLEX: ComplexAbundance,
    COMPOSITE: CompositeAbundance
}
