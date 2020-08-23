# -*- coding: utf-8 -*-

"""Constants for PyBEL tests."""

import logging

from pybel.constants import *
from pybel.dsl import (
    Abundance, BiologicalProcess, ComplexAbundance, CompositeAbundance, EnumeratedFusionRange, Fragment, Gene,
    GeneFusion, GeneModification, Hgvs, HgvsReference, HgvsUnspecified, MicroRna, NamedComplexAbundance, Pathology,
    Protein, ProteinFusion, ProteinModification, Reaction, Rna, RnaFusion, secretion, translocation,
)
from pybel.dsl.namespaces import hgnc
from pybel.language import activity_mapping, citation_dict, compartment_mapping

logger = logging.getLogger(__name__)

expected_test_simple_metadata = {
    METADATA_NAME: "PyBEL Test Simple",
    METADATA_DESCRIPTION: "Made for testing PyBEL parsing",
    METADATA_VERSION: "1.6.0",
    METADATA_COPYRIGHT: "Copyright (c) Charles Tapley Hoyt. All Rights Reserved.",
    METADATA_AUTHORS: "Charles Tapley Hoyt",
    METADATA_LICENSES: "WTF License",
    METADATA_CONTACT: "cthoyt@gmail.com",
    METADATA_PROJECT: 'PyBEL Testing',
}

expected_test_thorough_metadata = {
    METADATA_NAME: "PyBEL Test Thorough",
    METADATA_DESCRIPTION: "Statements made up to contain many conceivable variants of nodes from BEL",
    METADATA_VERSION: "1.0.0",
    METADATA_COPYRIGHT: "Copyright (c) Charles Tapley Hoyt. All Rights Reserved.",
    METADATA_AUTHORS: "Charles Tapley Hoyt",
    METADATA_LICENSES: "WTF License",
    METADATA_CONTACT: "cthoyt@gmail.com",
}

citation_1 = citation_dict(namespace=CITATION_TYPE_PUBMED, identifier='123455')
citation_2 = citation_dict(namespace=CITATION_TYPE_PUBMED, identifier='123456')

evidence_1 = "Evidence 1"
dummy_evidence = 'These are mostly made up'

akt1 = hgnc(name='AKT1')
egfr = hgnc(name='EGFR')
fadd = hgnc(name='FADD')
casp8 = hgnc(name='CASP8')
mia = hgnc(name='MIA')

il6 = Protein('HGNC', 'IL6')

adgrb1 = Protein(namespace='HGNC', name='ADGRB1')
adgrb2 = Protein(namespace='HGNC', name='ADGRB2')
adgrb_complex = ComplexAbundance([adgrb1, adgrb2])
achlorhydria = Pathology(namespace='MESHD', name='Achlorhydria')

akt1_rna = akt1.get_rna()
akt1_gene = akt1_rna.get_gene()
akt_methylated = akt1_gene.with_variants(GeneModification('Me'))
akt1_phe_508_del = akt1_gene.with_variants(Hgvs('p.Phe508del'))

cftr = hgnc(name='CFTR')
cftr_protein_unspecified_variant = cftr.with_variants(HgvsUnspecified())
cftr_protein_phe_508_del = cftr.with_variants(Hgvs('p.Phe508del'))

adenocarcinoma = Pathology('MESHD', 'Adenocarcinoma')
interleukin_23_complex = NamedComplexAbundance('GO', 'interleukin-23 complex')

oxygen_atom = Abundance(namespace='CHEBI', name='oxygen atom')
hydrogen_peroxide = Abundance('CHEBI', 'hydrogen peroxide')

tmprss2_gene = Gene('HGNC', 'TMPRSS2')

tmprss2_erg_gene_fusion = GeneFusion(
    partner_5p=tmprss2_gene,
    range_5p=EnumeratedFusionRange('c', 1, 79),
    partner_3p=Gene('HGNC', 'ERG'),
    range_3p=EnumeratedFusionRange('c', 312, 5034)
)

bcr_jak2_gene_fusion = GeneFusion(
    partner_5p=Gene('HGNC', 'BCR'),
    range_5p=EnumeratedFusionRange('c', '?', 1875),
    partner_3p=Gene('HGNC', 'JAK2'),
    range_3p=EnumeratedFusionRange('c', 2626, '?'),
)

chchd4_aifm1_gene_fusion = GeneFusion(
    partner_5p=Gene('HGNC', 'CHCHD4'),
    partner_3p=Gene('HGNC', 'AIFM1'),
)

tmprss2_erg_protein_fusion = ProteinFusion(
    partner_5p=Protein('HGNC', 'TMPRSS2'),
    range_5p=EnumeratedFusionRange('p', 1, 79),
    partner_3p=Protein('HGNC', 'ERG'),
    range_3p=EnumeratedFusionRange('p', 312, 5034)
)

bcr_jak2_protein_fusion = ProteinFusion(
    partner_5p=Protein('HGNC', 'BCR'),
    range_5p=EnumeratedFusionRange('p', '?', 1875),
    partner_3p=Protein('HGNC', 'JAK2'),
    range_3p=EnumeratedFusionRange('p', 2626, '?')
)

chchd4_aifm1_protein_fusion = ProteinFusion(
    Protein('HGNC', 'CHCHD4'),
    Protein('HGNC', 'AIFM1')
)

bcr_jak2_rna_fusion = RnaFusion(
    partner_5p=Rna('HGNC', 'BCR'),
    range_5p=EnumeratedFusionRange('r', '?', 1875),
    partner_3p=Rna('HGNC', 'JAK2'),
    range_3p=EnumeratedFusionRange('r', 2626, '?')
)

chchd4_aifm1_rna_fusion = RnaFusion(
    partner_5p=Rna('HGNC', 'CHCHD4'),
    partner_3p=Rna('HGNC', 'AIFM1')
)

tmprss2_erg_rna_fusion = RnaFusion(
    partner_5p=Rna('HGNC', 'TMPRSS2'),
    range_5p=EnumeratedFusionRange('r', 1, 79),
    partner_3p=Rna('HGNC', 'ERG'),
    range_3p=EnumeratedFusionRange('r', 312, 5034)
)
tmprss2_erg_rna_fusion_unspecified = RnaFusion(
    partner_5p=Rna('HGNC', 'TMPRSS2'),
    partner_3p=Rna('HGNC', 'ERG')
)

BEL_THOROUGH_NODES = {
    oxygen_atom,
    tmprss2_erg_rna_fusion,
    tmprss2_erg_rna_fusion_unspecified,
    akt_methylated,
    bcr_jak2_rna_fusion,
    chchd4_aifm1_rna_fusion,
    akt1_gene,
    akt1_phe_508_del,
    akt1,
    Gene('HGNC', 'AKT1', variants=Hgvs('c.308G>A')),
    tmprss2_erg_gene_fusion,
    Gene('HGNC', 'AKT1', variants=[Hgvs('c.1521_1523delCTT'), Hgvs('c.308G>A'), Hgvs('p.Phe508del')]),
    MicroRna('HGNC', 'MIR21'),
    bcr_jak2_gene_fusion,
    Gene('HGNC', 'CFTR', variants=Hgvs('c.1521_1523delCTT')),
    Gene('HGNC', 'CFTR'),
    Gene('HGNC', 'CFTR', variants=Hgvs('g.117199646_117199648delCTT')),
    Gene('HGNC', 'CFTR', variants=Hgvs('c.1521_1523delCTT')),
    Protein('HGNC', 'AKT1', variants=ProteinModification('Ph', 'Ser', 473)),
    MicroRna('HGNC', 'MIR21', variants=Hgvs('p.Phe508del')),
    Protein('HGNC', 'AKT1', variants=Hgvs('p.C40*')),
    Protein('HGNC', 'AKT1', variants=[Hgvs('p.Ala127Tyr'), ProteinModification('Ph', 'Ser')]),
    chchd4_aifm1_gene_fusion,
    tmprss2_erg_protein_fusion,
    Protein('HGNC', 'AKT1', variants=Hgvs('p.Arg1851*')),
    bcr_jak2_protein_fusion,
    Protein('HGNC', 'AKT1', variants=Hgvs('p.40*')),
    chchd4_aifm1_protein_fusion,
    Protein('HGNC', 'CFTR', variants=HgvsReference()),
    cftr,
    egfr,
    cftr_protein_unspecified_variant,
    adenocarcinoma,
    cftr_protein_phe_508_del,
    Protein('HGNC', 'MIA', variants=Fragment(5, 20)),
    mia,
    interleukin_23_complex,
    Protein('HGNC', 'MIA', variants=Fragment(1, '?')),
    Protein('HGNC', 'MIA', variants=Fragment()),
    Protein('HGNC', 'MIA', variants=Fragment(description='55kD')),
    Protein('HGNC', 'CFTR', variants=Hgvs('p.Gly576Ala')),
    akt1_rna,
    Rna('HGNC', 'AKT1', variants=[Hgvs('c.1521_1523delCTT'), Hgvs('p.Phe508del')]),
    Gene('HGNC', 'NCF1'),
    ComplexAbundance([
        Gene('HGNC', 'NCF1'),
        Protein('HGNC', 'HBP1')
    ]),
    Protein('HGNC', 'HBP1'),
    ComplexAbundance([Protein('HGNC', 'FOS'), Protein('HGNC', 'JUN')]),
    Protein('HGNC', 'FOS'),
    Protein('HGNC', 'JUN'),
    Rna('HGNC', 'CFTR', variants=Hgvs('r.1521_1523delcuu')),
    Rna('HGNC', 'CFTR'),
    Rna('HGNC', 'CFTR', variants=Hgvs('r.1653_1655delcuu')),
    CompositeAbundance([
        interleukin_23_complex,
        il6
    ]),
    il6,
    BiologicalProcess('GO', 'cell cycle arrest'),
    hydrogen_peroxide,
    Protein('HGNC', 'CAT'),
    Gene('HGNC', 'CAT'),
    Protein('HGNC', 'HMGCR'),
    BiologicalProcess('GO', 'cholesterol biosynthetic process'),
    Gene('HGNC', 'APP', variants=Hgvs('c.275341G>C')),
    Gene('HGNC', 'APP'),
    Pathology('MESHD', 'Alzheimer Disease'),
    ComplexAbundance([Protein('HGNC', 'F3'), Protein('HGNC', 'F7')]),
    Protein('HGNC', 'F3'),
    Protein('HGNC', 'F7'),
    Protein('HGNC', 'F9'),
    Protein('HGNC', 'GSK3B', variants=ProteinModification('Ph', 'Ser', 9)),
    Protein('HGNC', 'GSK3B'),
    Pathology('MESHD', 'Psoriasis'),
    Pathology('MESHD', 'Skin Diseases'),
    Reaction(
        reactants=[
            Abundance('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
            Abundance('CHEBI', 'NADPH'),
            Abundance('CHEBI', 'hydron')
        ],
        products=[
            Abundance('CHEBI', 'NADP(+)'),
            Abundance('CHEBI', 'mevalonate')
        ]
    ),
    Abundance('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
    Abundance('CHEBI', 'NADPH'),
    Abundance('CHEBI', 'hydron'),
    Abundance('CHEBI', 'mevalonate'),
    Abundance('CHEBI', 'NADP(+)'),
    Abundance('CHEBI', 'nitric oxide'),
    ComplexAbundance([
        Protein('HGNC', 'ITGAV'),
        Protein('HGNC', 'ITGB3')
    ]),
    Protein('HGNC', 'ITGAV'),
    Protein('HGNC', 'ITGB3'),
    Protein('HGNC', 'FADD'),
    Abundance('TESTNS2', 'Abeta_42'),
    Protein('TESTNS2', 'GSK3 Family'),
    Protein('HGNC', 'PRKCA'),
    Protein('HGNC', 'CDK5'),
    Protein('HGNC', 'CASP8'),
    Protein('HGNC', 'AKT1',
            variants=ProteinModification(namespace='TESTNS2', name='PhosRes', code='Ser', position=473)),
    Protein('HGNC', 'HRAS', variants=ProteinModification('Palm')),
    BiologicalProcess('GO', 'apoptotic process'),
    CompositeAbundance([
        Abundance('TESTNS2', 'Abeta_42'),
        Protein('HGNC', 'CASP8'),
        Protein('HGNC', 'FADD')
    ]),
    Reaction(
        reactants=[Protein('HGNC', 'CDK5R1')],
        products=[Protein('HGNC', 'CDK5')],
    ),
    Protein('HGNC', 'PRKCB'),
    NamedComplexAbundance('TESTNS2', 'AP-1 Complex'),
    Protein('HGNC', 'PRKCE'),
    Protein('HGNC', 'PRKCD'),
    Protein('TESTNS2', 'CAPN Family'),
    Gene('TESTNS2', 'AKT1 ortholog'),
    Protein('HGNC', 'HRAS'),
    Protein('HGNC', 'CDK5R1'),
    Protein('TESTNS2', 'PRKC'),
    BiologicalProcess('GO', 'neuron apoptotic process'),
    Protein('HGNC', 'MAPT', variants=ProteinModification('Ph')),
    Protein('HGNC', 'MAPT'),
    Gene('HGNC', 'ARRDC2'),
    Gene('HGNC', 'ARRDC3'),
    Gene('dbSNP', 'rs123456')
}

BEL_THOROUGH_EDGES = [
    (Gene('HGNC', 'AKT1', variants=Hgvs('p.Phe508del')), akt1, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: DIRECTLY_DECREASES,
    }),
    (akt1, Protein('HGNC', 'AKT1', variants=ProteinModification('Ph', 'Ser', 473)), {
        RELATION: HAS_VARIANT,
    }),
    (akt1, Protein('HGNC', 'AKT1', variants=Hgvs('p.C40*')), {
        RELATION: HAS_VARIANT,
    }),
    (akt1,
     Protein('HGNC', 'AKT1', variants=[Hgvs('p.Ala127Tyr'), ProteinModification('Ph', 'Ser')]), {
         RELATION: HAS_VARIANT,
     }),
    (akt1,
     Protein('HGNC', 'AKT1', variants=[Hgvs('p.Ala127Tyr'), ProteinModification('Ph', 'Ser')]), {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: DIRECTLY_DECREASES,
         SOURCE_MODIFIER: {LOCATION: {NAMESPACE: 'GO', NAME: 'intracellular'}},
         TARGET_MODIFIER: {LOCATION: {NAMESPACE: 'GO', NAME: 'intracellular'}},
     }),
    (akt1, Protein('HGNC', 'AKT1', variants=Hgvs('p.Arg1851*')), {
        RELATION: HAS_VARIANT,
    }),
    (akt1, Protein('HGNC', 'AKT1', variants=Hgvs('p.40*')), {
        RELATION: HAS_VARIANT,
    }),
    (akt1, Protein('HGNC', 'MIA', variants=Fragment()), {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        SOURCE_MODIFIER: {MODIFIER: DEGRADATION},
    }),
    (akt1, Protein('HGNC', 'CFTR', variants=Hgvs('p.Gly576Ala')), {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
    }),
    (akt1, Rna('HGNC', 'CFTR', variants=Hgvs('r.1521_1523delcuu')), {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        SOURCE_MODIFIER: {MODIFIER: ACTIVITY, EFFECT: activity_mapping['kin']},
    }),
    (akt1, Rna('HGNC', 'CFTR', variants=Hgvs('r.1653_1655delcuu')), {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        SOURCE_MODIFIER: {MODIFIER: ACTIVITY},
    }),
    (akt1, egfr, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        SOURCE_MODIFIER: {
            MODIFIER: ACTIVITY,
            EFFECT: activity_mapping['cat'],
        },
        TARGET_MODIFIER: {MODIFIER: DEGRADATION},
    }),
    (akt1, egfr, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        SOURCE_MODIFIER: {
            MODIFIER: ACTIVITY,
            EFFECT: activity_mapping['kin'],
        },
        TARGET_MODIFIER: secretion(),
    }),
    (Gene('HGNC', 'AKT1', variants=Hgvs('c.308G>A')), tmprss2_erg_gene_fusion, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: CAUSES_NO_CHANGE,
    }),
    (Gene('HGNC', 'AKT1', variants=Hgvs('c.308G>A')),
     Gene('HGNC', 'AKT1', variants=[Hgvs('c.1521_1523delCTT'), Hgvs('c.308G>A'), Hgvs('p.Phe508del')]), {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
         SOURCE_MODIFIER: {LOCATION: {NAMESPACE: 'GO', NAME: 'intracellular'}},
     }),
    (MicroRna('HGNC', 'MIR21'), bcr_jak2_gene_fusion,
     {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: DIRECTLY_INCREASES,
     }),
    (MicroRna('HGNC', 'MIR21'), Protein('HGNC', 'AKT1', variants=ProteinModification('Ph', 'Ser', 473)),
     {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: DECREASES,
         SOURCE_MODIFIER: {LOCATION: {NAMESPACE: 'GO', NAME: 'intracellular'}},
     }),
    (MicroRna('HGNC', 'MIR21'), MicroRna('HGNC', 'MIR21', variants=Hgvs('p.Phe508del')), {
        RELATION: HAS_VARIANT,
    }),
    (Gene('HGNC', 'CFTR', variants=Hgvs('c.1521_1523delCTT')), akt1,
     {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
         TARGET_MODIFIER: {MODIFIER: DEGRADATION},
     }),
    (Gene('HGNC', 'CFTR'), Gene('HGNC', 'CFTR', variants=Hgvs('c.1521_1523delCTT')), {
        RELATION: HAS_VARIANT,
    }),
    (Gene('HGNC', 'CFTR'), Gene('HGNC', 'CFTR', variants=Hgvs('g.117199646_117199648delCTT')), {
        RELATION: HAS_VARIANT,
    }),
    (Gene('HGNC', 'CFTR'), Gene('HGNC', 'CFTR', variants=Hgvs('c.1521_1523delCTT')), {
        RELATION: HAS_VARIANT,
    }),
    (Gene('HGNC', 'CFTR', variants=Hgvs('g.117199646_117199648delCTT')),
     Gene('HGNC', 'CFTR', variants=Hgvs('c.1521_1523delCTT')), {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
     }),
    (MicroRna('HGNC', 'MIR21', variants=Hgvs('p.Phe508del')), Protein('HGNC', 'AKT1', variants=Hgvs('p.C40*')),
     {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
         SOURCE_MODIFIER: {LOCATION: {NAMESPACE: 'GO', NAME: 'intracellular'}},
     }),
    (chchd4_aifm1_gene_fusion, tmprss2_erg_protein_fusion, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
    }),
    (Protein('HGNC', 'AKT1', variants=Hgvs('p.Arg1851*')), bcr_jak2_protein_fusion, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
    }),
    (Protein('HGNC', 'AKT1', variants=Hgvs('p.40*')), chchd4_aifm1_protein_fusion,
     {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
     }),
    (Protein('HGNC', 'CFTR', variants=HgvsReference()), egfr, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        TARGET_MODIFIER: translocation(INTRACELLULAR, CELL_SURFACE),
    }),
    (cftr, Protein('HGNC', 'CFTR', variants=Hgvs('=')), {
        RELATION: HAS_VARIANT,
    }),
    (cftr, Protein('HGNC', 'CFTR', variants=Hgvs('?')), {
        RELATION: HAS_VARIANT,
    }),
    (cftr, Protein('HGNC', 'CFTR', variants=Hgvs('p.Phe508del')), {
        RELATION: HAS_VARIANT,
    }),
    (cftr, Protein('HGNC', 'CFTR', variants=Hgvs('p.Gly576Ala')), {
        RELATION: HAS_VARIANT,
    }),
    (mia, Protein('HGNC', 'MIA', variants=Fragment(5, 20)), {
        RELATION: HAS_VARIANT,
    }),
    (mia, Protein('HGNC', 'MIA', variants=Fragment(1, '?')), {
        RELATION: HAS_VARIANT,
    }),
    (mia, Protein('HGNC', 'MIA', variants=Fragment()), {
        RELATION: HAS_VARIANT,
    }),
    (mia, Protein('HGNC', 'MIA', variants=Fragment(description='55kD')), {
        RELATION: HAS_VARIANT,
    }),
    (akt1_rna, Rna('HGNC', 'AKT1', variants=[Hgvs('c.1521_1523delCTT'), Hgvs('p.Phe508del')]), {
        RELATION: HAS_VARIANT,
    }),
    (akt1_rna, akt1, {
        RELATION: TRANSLATED_TO,
    }),
    (Gene('HGNC', 'APP'), Gene('HGNC', 'APP', variants=Hgvs('c.275341G>C')), {
        RELATION: HAS_VARIANT,
    }),
    (
        Protein('HGNC', 'F3'),
        ComplexAbundance([Protein('HGNC', 'F3'), Protein('HGNC', 'F7')]),
        {
            RELATION: PART_OF,
        }
    ),
    (
        Protein('HGNC', 'F7'),
        ComplexAbundance([Protein('HGNC', 'F3'), Protein('HGNC', 'F7')]),
        {
            RELATION: PART_OF,
        }
    ),
    (Protein('HGNC', 'GSK3B'), Protein('HGNC', 'GSK3B', variants=ProteinModification('Ph', 'Ser', 9)), {
        RELATION: HAS_VARIANT,
    }),
    (Pathology('MESHD', 'Psoriasis'), Pathology('MESHD', 'Skin Diseases'), {
        RELATION: IS_A,
    }),
    (
        Protein('HGNC', 'HBP1'),
        ComplexAbundance([Gene('HGNC', 'NCF1'), Protein('HGNC', 'HBP1')]),
        {
            RELATION: PART_OF,
        },
    ),
    (
        Gene('HGNC', 'NCF1'),
        ComplexAbundance([Gene('HGNC', 'NCF1'), Protein('HGNC', 'HBP1')]),
        {
            RELATION: PART_OF,
        },
    ),
    (
        Protein('HGNC', 'FOS'),
        ComplexAbundance([Protein('HGNC', 'FOS'), Protein('HGNC', 'JUN')]),
        {
            RELATION: PART_OF,
        }
    ),
    (
        Protein('HGNC', 'JUN'),
        ComplexAbundance([Protein('HGNC', 'FOS'), Protein('HGNC', 'JUN')]),
        {
            RELATION: PART_OF,
        }
    ),
    (Rna('HGNC', 'CFTR'), Rna('HGNC', 'CFTR', variants=Hgvs('r.1521_1523delcuu')), {
        RELATION: HAS_VARIANT,
    }),
    (Rna('HGNC', 'CFTR'), Rna('HGNC', 'CFTR', variants=Hgvs('r.1653_1655delcuu')), {
        RELATION: HAS_VARIANT,
    }),
    (
        il6,
        CompositeAbundance([interleukin_23_complex, il6]),
        {
            RELATION: PART_OF,
        }
    ),
    (
        interleukin_23_complex,
        CompositeAbundance([interleukin_23_complex, il6]),
        {
            RELATION: PART_OF,
        }
    ),
    (Protein('HGNC', 'CFTR', variants=Hgvs('?')), Pathology('MESHD', 'Adenocarcinoma'), {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
    }),
    (Rna('HGNC', 'AKT1', variants=[Hgvs('c.1521_1523delCTT'), Hgvs('p.Phe508del')]),
     tmprss2_erg_rna_fusion, {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: DIRECTLY_INCREASES,
     }),
    (RnaFusion(Rna('HGNC', 'TMPRSS2'), Rna('HGNC', 'ERG')),
     ComplexAbundance([Gene('HGNC', 'NCF1'), Protein('HGNC', 'HBP1')]), {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
     }),
    (Protein('HGNC', 'MIA', variants=Fragment(5, 20)), NamedComplexAbundance('GO', 'interleukin-23 complex'), {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        TARGET_MODIFIER: secretion(),
    }),
    (Protein('HGNC', 'MIA', variants=Fragment(1, '?')), egfr, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        TARGET_MODIFIER: {
            MODIFIER: TRANSLOCATION,
            EFFECT: {
                FROM_LOC: {NAMESPACE: 'GO', NAME: 'cell surface'},
                TO_LOC: {NAMESPACE: 'GO', NAME: 'endosome'}
            }
        },
    }),
    (akt1_rna, egfr, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        TARGET_MODIFIER: {
            MODIFIER: TRANSLOCATION, EFFECT: {
                FROM_LOC: {NAMESPACE: 'GO', NAME: 'cell surface'},
                TO_LOC: {NAMESPACE: 'GO', NAME: 'endosome'}
            }
        },
    }),
    (RnaFusion(Rna('HGNC', 'CHCHD4'), Rna('HGNC', 'AIFM1'), ),
     ComplexAbundance([Protein('HGNC', 'FOS'), Protein('HGNC', 'JUN')]),
     {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
     }),
    (CompositeAbundance([interleukin_23_complex, il6]),
     BiologicalProcess('GO', 'cell cycle arrest'), {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: DECREASES,
     }),
    (Protein('HGNC', 'CAT'), hydrogen_peroxide, {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: DIRECTLY_DECREASES,
        SOURCE_MODIFIER: {LOCATION: {NAMESPACE: 'GO', NAME: 'intracellular'}},
    }),
    (Gene('HGNC', 'CAT'), hydrogen_peroxide, {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: DIRECTLY_DECREASES,
        SOURCE_MODIFIER: {LOCATION: {NAMESPACE: 'GO', NAME: 'intracellular'}},
    }),
    (Protein('HGNC', 'HMGCR'), BiologicalProcess('GO', 'cholesterol biosynthetic process'), {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: RATE_LIMITING_STEP_OF,
        SOURCE_MODIFIER: {MODIFIER: ACTIVITY, EFFECT: activity_mapping['cat']},
    }),
    (Gene('HGNC', 'APP', variants=Hgvs('c.275341G>C')), Pathology('MESHD', 'Alzheimer Disease'),
     {
         EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
         CITATION: citation_2,
         RELATION: CAUSES_NO_CHANGE,
     }),

    (ComplexAbundance([Protein('HGNC', 'F3'), Protein('HGNC', 'F7')]), Protein('HGNC', 'F9'), {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: REGULATES,
        SOURCE_MODIFIER: {MODIFIER: ACTIVITY, EFFECT: activity_mapping['pep']},
        TARGET_MODIFIER: {MODIFIER: ACTIVITY, EFFECT: activity_mapping['pep']},
    }),
    (Protein('HGNC', 'GSK3B', variants=ProteinModification('Ph', 'Ser', 9)), Protein('HGNC', 'GSK3B'), {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: POSITIVE_CORRELATION,
        TARGET_MODIFIER: {MODIFIER: ACTIVITY, EFFECT: activity_mapping['kin']},
    }),

    (Protein('HGNC', 'GSK3B'), Protein('HGNC', 'GSK3B', variants=ProteinModification('Ph', 'Ser', 9)), {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: POSITIVE_CORRELATION,
        SOURCE_MODIFIER: {MODIFIER: ACTIVITY, EFFECT: activity_mapping['kin']},
    }),

    (Reaction(
        reactants=(
            Abundance('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
            Abundance('CHEBI', 'NADPH'),
            Abundance('CHEBI', 'hydron')
        ),
        products=(
            Abundance('CHEBI', 'NADP(+)'),
            Abundance('CHEBI', 'mevalonate')
        )
    ),
     Abundance('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'), {
         RELATION: HAS_REACTANT,
     }),
    (Reaction(
        reactants=(
            Abundance('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
            Abundance('CHEBI', 'NADPH'),
            Abundance('CHEBI', 'hydron')
        ),
        products=(
            Abundance('CHEBI', 'NADP(+)'),
            Abundance('CHEBI', 'mevalonate')
        )
    ),
     Abundance('CHEBI', 'NADPH'), {
         RELATION: HAS_REACTANT,
     }),
    (
        Reaction(
            reactants=(
                Abundance('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
                Abundance('CHEBI', 'NADPH'),
                Abundance('CHEBI', 'hydron')
            ),
            products=(
                Abundance('CHEBI', 'NADP(+)'),
                Abundance('CHEBI', 'mevalonate')
            )
        ),
        Abundance('CHEBI', 'hydron'), {
            RELATION: HAS_REACTANT,
        }),
    (Reaction(
        reactants=(
            Abundance('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
            Abundance('CHEBI', 'NADPH'),
            Abundance('CHEBI', 'hydron')
        ),
        products=(
            Abundance('CHEBI', 'NADP(+)'),
            Abundance('CHEBI', 'mevalonate'))
    ),
     Abundance('CHEBI', 'mevalonate'), {
         RELATION: HAS_PRODUCT,
     }),
    (Reaction(
        reactants=(
            Abundance('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
            Abundance('CHEBI', 'NADPH'),
            Abundance('CHEBI', 'hydron')
        ),
        products=(
            Abundance('CHEBI', 'NADP(+)'),
            Abundance('CHEBI', 'mevalonate')
        )
    ),
     Abundance('CHEBI', 'NADP(+)'), {
         RELATION: HAS_PRODUCT,
     }),
    (Reaction(
        reactants=(
            Abundance('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
            Abundance('CHEBI', 'NADPH'),
            Abundance('CHEBI', 'hydron')
        ),
        products=(
            Abundance('CHEBI', 'NADP(+)'),
            Abundance('CHEBI', 'mevalonate')
        )
    ),
     BiologicalProcess('GO', 'cholesterol biosynthetic process'),
     {
         EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
         CITATION: citation_2,
         RELATION: SUBPROCESS_OF,
     }),
    (Abundance('CHEBI', 'nitric oxide'),
     ComplexAbundance([Protein('HGNC', 'ITGAV'), Protein('HGNC', 'ITGB3')]), {
         EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
         CITATION: citation_2,
         RELATION: INCREASES,
         TARGET_MODIFIER: {
             MODIFIER: TRANSLOCATION,
             EFFECT: {
                 FROM_LOC: compartment_mapping['intracellular'],
                 TO_LOC: compartment_mapping['cell surface'],
             }
         },
     }),
    (
        Protein('HGNC', 'ITGAV'),
        ComplexAbundance([Protein('HGNC', 'ITGAV'), Protein('HGNC', 'ITGB3')]),
        {
            RELATION: PART_OF,
        }
    ),
    (
        Protein('HGNC', 'ITGB3'),
        ComplexAbundance([Protein('HGNC', 'ITGAV'), Protein('HGNC', 'ITGB3')]),
        {
            RELATION: PART_OF,
        }
    ),
    (Gene('HGNC', 'ARRDC2'), Gene('HGNC', 'ARRDC3'), {
        RELATION: EQUIVALENT_TO,
    }),
    (Gene('HGNC', 'ARRDC3'), Gene('HGNC', 'ARRDC2'), {
        RELATION: EQUIVALENT_TO,
        CITATION: citation_2,
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification'
    }),
    (Gene('dbSNP', 'rs123456'), Gene('HGNC', 'CFTR', variants=Hgvs('c.1521_1523delCTT')), {
        RELATION: ASSOCIATION,
        CITATION: citation_2,
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification'
    }),
    (Gene('HGNC', 'CFTR', variants=Hgvs('c.1521_1523delCTT')), Gene('dbSNP', 'rs123456'), {
        RELATION: ASSOCIATION,
        CITATION: citation_2,
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification'
    }),
]
