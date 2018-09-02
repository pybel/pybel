# -*- coding: utf-8 -*-

"""Convenient wrappers for DSL classes.

Also provided for backwards compatibility.
"""

from .node_classes import (
    Abundance, BiologicalProcess, ComplexAbundance, CompositeAbundance, EnumeratedFusionRange, Fragment, Gene,
    GeneFusion, GeneModification, Hgvs, HgvsReference, HgvsUnspecified, MicroRna, MissingFusionRange,
    NamedComplexAbundance, Pathology, Protein, ProteinFusion, ProteinModification, ProteinSubstitution, Reaction, Rna,
    RnaFusion,
)

__all__ = [
    'abundance',
    'gene',
    'rna',
    'mirna',
    'protein',
    'complex_abundance',
    'composite_abundance',
    'bioprocess',
    'pathology',
    'named_complex_abundance',
    'reaction',
    'pmod',
    'gmod',
    'hgvs',
    'hgvs_reference',
    'hgvs_unspecified',
    'protein_substitution',
    'fragment',
    'fusion_range',
    'missing_fusion_range',
    'protein_fusion',
    'rna_fusion',
    'gene_fusion',
]

abundance = Abundance

bioprocess = BiologicalProcess

pathology = Pathology

pmod = ProteinModification

gmod = GeneModification

hgvs = Hgvs
hgvs_unspecified = HgvsUnspecified
hgvs_reference = HgvsReference

protein_substitution = ProteinSubstitution

fragment = Fragment

gene = Gene

rna = Rna

mirna = MicroRna

protein = Protein

reaction = Reaction

complex_abundance = ComplexAbundance

named_complex_abundance = NamedComplexAbundance

composite_abundance = CompositeAbundance

missing_fusion_range = MissingFusionRange

fusion_range = EnumeratedFusionRange

protein_fusion = ProteinFusion

rna_fusion = RnaFusion

gene_fusion = GeneFusion
