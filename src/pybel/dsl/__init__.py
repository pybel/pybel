# -*- coding: utf-8 -*-

"""PyBEL implements an internal domain-specific language (DSL).

This enables you to write BEL using Python scripts. Even better,
you can programatically generate BEL using Python. See the
Bio2BEL `paper <https://doi.org/10.1101/631812>`_ and `repository <https://github.com/bio2bel/bio2bel>`_
for many examples.

Internally, the BEL parser converts BEL script into the BEL DSL
then adds it to a BEL graph object. When you iterate through
the :class:`pybel.BELGraph`, the nodes are instances of subclasses
of :class:`pybel.dsl.BaseEntity`.
"""

from .constants import FUNC_TO_DSL, FUNC_TO_FUSION_DSL, FUNC_TO_LIST_DSL
from .edges import activity, cell_surface_expression, degradation, location, secretion, translocation
from .exc import InferCentralDogmaException, ListAbundanceEmptyException, PyBELDSLException, ReactionEmptyException
from .namespaces import chebi, hgnc, mirbase
from .node_classes import (
    Abundance, BaseAbundance, BaseConcept, BaseEntity, BiologicalProcess, CentralDogma, ComplexAbundance,
    CompositeAbundance, Entity, EntityVariant, EnumeratedFusionRange, Fragment, FusionBase, FusionRangeBase, Gene,
    GeneFusion, GeneModification, Hgvs, HgvsReference, HgvsUnspecified, ListAbundance, MicroRna, MissingFusionRange,
    NamedComplexAbundance, Pathology, Population, Protein, ProteinFusion, ProteinModification, ProteinSubstitution,
    Reaction, Rna, RnaFusion, Transcribable, Variant,
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
