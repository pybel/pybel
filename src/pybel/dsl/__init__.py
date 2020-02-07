# -*- coding: utf-8 -*-

"""An internal domain-specific language (DSL) for BEL."""

from .constants import FUNC_TO_DSL, FUNC_TO_FUSION_DSL, FUNC_TO_LIST_DSL
from .edges import activity, cell_surface_expression, degradation, location, secretion, translocation
from .exc import InferCentralDogmaException, ListAbundanceEmptyException, PyBELDSLException, ReactionEmptyException
from .namespaces import chebi, hgnc, mirbase
from .node_classes import (
    Abundance, BaseAbundance, BaseEntity, BiologicalProcess, CentralDogma, ComplexAbundance, CompositeAbundance, Entity,
    EnumeratedFusionRange, Fragment, FusionBase, FusionRangeBase, Gene, GeneFusion, GeneModification, Hgvs,
    HgvsReference, HgvsUnspecified, ListAbundance, MicroRna, MissingFusionRange, NamedComplexAbundance, Pathology,
    Population, Protein, ProteinFusion, ProteinModification, ProteinSubstitution, Reaction, Rna, RnaFusion, Variant,
)

entity = Entity

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
