# -*- coding: utf-8 -*-

"""Constants for PyBEL tests."""

import logging

from pybel.constants import *
from pybel.dsl import *
from pybel.dsl.namespaces import hgnc

log = logging.getLogger(__name__)

expected_test_simple_metadata = {
    METADATA_NAME: "PyBEL Test Simple",
    METADATA_DESCRIPTION: "Made for testing PyBEL parsing",
    METADATA_VERSION: "1.6.0",
    METADATA_COPYRIGHT: "Copyright (c) Charles Tapley Hoyt. All Rights Reserved.",
    METADATA_AUTHORS: "Charles Tapley Hoyt",
    METADATA_LICENSES: "WTF License",
    METADATA_CONTACT: "charles.hoyt@scai.fraunhofer.de",
    METADATA_PROJECT: 'PyBEL Testing',
}

expected_test_thorough_metadata = {
    METADATA_NAME: "PyBEL Test Thorough",
    METADATA_DESCRIPTION: "Statements made up to contain many conceivable variants of nodes from BEL",
    METADATA_VERSION: "1.0.0",
    METADATA_COPYRIGHT: "Copyright (c) Charles Tapley Hoyt. All Rights Reserved.",
    METADATA_AUTHORS: "Charles Tapley Hoyt",
    METADATA_LICENSES: "WTF License",
    METADATA_CONTACT: "charles.hoyt@scai.fraunhofer.de"
}

citation_1 = {
    CITATION_TYPE: 'PubMed',
    CITATION_NAME: 'That one article from last week',
    CITATION_REFERENCE: '123455'
}

citation_2 = {
    CITATION_TYPE: 'PubMed',
    CITATION_NAME: 'That one article from last week #2',
    CITATION_REFERENCE: '123456'
}

evidence_1 = "Evidence 1"
dummy_evidence = 'These are mostly made up'

akt1 = hgnc(name='AKT1')
egfr = hgnc(name='EGFR')
fadd = hgnc(name='FADD')
casp8 = hgnc(name='CASP8')
mia = hgnc(name='MIA')

il6 = protein('HGNC', 'IL6')

adgrb1 = protein(namespace='HGNC', name='ADGRB1')
adgrb2 = protein(namespace='HGNC', name='ADGRB2')
adgrb_complex = complex_abundance([adgrb1, adgrb2])
achlorhydria = pathology(namespace='MESHD', name='Achlorhydria')

akt1_rna = akt1.get_rna()
akt1_gene = akt1_rna.get_gene()
akt_methylated = akt1_gene.with_variants(gmod('Me'))
akt1_phe_508_del = akt1_gene.with_variants(hgvs('p.Phe508del'))

cftr = hgnc('CFTR')
cftr_protein_unspecified_variant = cftr.with_variants(hgvs_unspecified())
cftr_protein_phe_508_del = cftr.with_variants(hgvs('p.Phe508del'))

adenocarcinoma = pathology('MESHD', 'Adenocarcinoma')
interleukin_23_complex = named_complex_abundance('GO', 'interleukin-23 complex')

oxygen_atom = abundance(namespace='CHEBI', name='oxygen atom')
hydrogen_peroxide = abundance('CHEBI', 'hydrogen peroxide')

tmprss2_gene = gene('HGNC', 'TMPRSS2')

tmprss2_erg_gene_fusion = gene_fusion(
    partner_5p=tmprss2_gene,
    range_5p=fusion_range('c', 1, 79),
    partner_3p=gene('HGNC', 'ERG'),
    range_3p=fusion_range('c', 312, 5034)
)

bcr_jak2_gene_fusion = gene_fusion(
    partner_5p=gene('HGNC', 'BCR'),
    range_5p=fusion_range('c', '?', 1875),
    partner_3p=gene('HGNC', 'JAK2'),
    range_3p=fusion_range('c', 2626, '?')
)

chchd4_aifm1_gene_fusion = gene_fusion(
    partner_5p=gene('HGNC', 'CHCHD4'),
    partner_3p=gene('HGNC', 'AIFM1')
)

tmprss2_erg_protein_fusion = protein_fusion(
    partner_5p=protein('HGNC', 'TMPRSS2'),
    range_5p=fusion_range('p', 1, 79),
    partner_3p=protein('HGNC', 'ERG'),
    range_3p=fusion_range('p', 312, 5034)
)

bcr_jak2_protein_fusion = protein_fusion(
    partner_5p=protein('HGNC', 'BCR'),
    range_5p=fusion_range('p', '?', 1875),
    partner_3p=protein('HGNC', 'JAK2'),
    range_3p=fusion_range('p', 2626, '?')
)

chchd4_aifm1_protein_fusion = protein_fusion(
    protein('HGNC', 'CHCHD4'),
    protein('HGNC', 'AIFM1')
)

bcr_jak2_rna_fusion = rna_fusion(
    partner_5p=rna('HGNC', 'BCR'),
    range_5p=fusion_range('r', '?', 1875),
    partner_3p=rna('HGNC', 'JAK2'),
    range_3p=fusion_range('r', 2626, '?')
)

chchd4_aifm1_rna_fusion = rna_fusion(
    partner_5p=rna('HGNC', 'CHCHD4'),
    partner_3p=rna('HGNC', 'AIFM1')
)

tmprss2_erg_rna_fusion = rna_fusion(
    partner_5p=rna('HGNC', 'TMPRSS2'),
    range_5p=fusion_range('r', 1, 79),
    partner_3p=rna('HGNC', 'ERG'),
    range_3p=fusion_range('r', 312, 5034)
)
tmprss2_erg_rna_fusion_unspecified = rna_fusion(
    partner_5p=rna('HGNC', 'TMPRSS2'),
    partner_3p=rna('HGNC', 'ERG')
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
    gene('HGNC', 'AKT1', variants=hgvs('c.308G>A')),
    tmprss2_erg_gene_fusion,
    gene('HGNC', 'AKT1', variants=[hgvs('c.1521_1523delCTT'), hgvs('c.308G>A'), hgvs('p.Phe508del')]),
    mirna('HGNC', 'MIR21'),
    bcr_jak2_gene_fusion,
    gene('HGNC', 'CFTR', variants=hgvs('c.1521_1523delCTT')),
    gene('HGNC', 'CFTR'),
    gene('HGNC', 'CFTR', variants=hgvs('g.117199646_117199648delCTT')),
    gene('HGNC', 'CFTR', variants=hgvs('c.1521_1523delCTT')),
    protein('HGNC', 'AKT1', variants=pmod('Ph', 'Ser', 473)),
    mirna('HGNC', 'MIR21', variants=hgvs('p.Phe508del')),
    protein('HGNC', 'AKT1', variants=hgvs('p.C40*')),
    protein('HGNC', 'AKT1', variants=[hgvs('p.Ala127Tyr'), pmod('Ph', 'Ser')]),
    chchd4_aifm1_gene_fusion,
    tmprss2_erg_protein_fusion,
    protein('HGNC', 'AKT1', variants=hgvs('p.Arg1851*')),
    bcr_jak2_protein_fusion,
    protein('HGNC', 'AKT1', variants=hgvs('p.40*')),
    chchd4_aifm1_protein_fusion,
    protein('HGNC', 'CFTR', variants=hgvs_reference()),
    cftr,
    egfr,
    cftr_protein_unspecified_variant,
    adenocarcinoma,
    cftr_protein_phe_508_del,
    protein('HGNC', 'MIA', variants=fragment(5, 20)),
    mia,
    interleukin_23_complex,
    protein('HGNC', 'MIA', variants=fragment(1, '?')),
    protein('HGNC', 'MIA', variants=fragment()),
    protein('HGNC', 'MIA', variants=fragment(description='55kD')),
    protein('HGNC', 'CFTR', variants=hgvs('p.Gly576Ala')),
    akt1_rna,
    rna('HGNC', 'AKT1', variants=[hgvs('c.1521_1523delCTT'), hgvs('p.Phe508del')]),
    gene('HGNC', 'NCF1'),
    complex_abundance([
        gene('HGNC', 'NCF1'),
        protein('HGNC', 'HBP1')
    ]),
    protein('HGNC', 'HBP1'),
    complex_abundance([protein('HGNC', 'FOS'), protein('HGNC', 'JUN')]),
    protein('HGNC', 'FOS'),
    protein('HGNC', 'JUN'),
    rna('HGNC', 'CFTR', variants=hgvs('r.1521_1523delcuu')),
    rna('HGNC', 'CFTR'),
    rna('HGNC', 'CFTR', variants=hgvs('r.1653_1655delcuu')),
    composite_abundance([
        interleukin_23_complex,
        il6
    ]),
    il6,
    bioprocess('GO', 'cell cycle arrest'),
    hydrogen_peroxide,
    protein('HGNC', 'CAT'),
    gene('HGNC', 'CAT'),
    protein('HGNC', 'HMGCR'),
    bioprocess('GO', 'cholesterol biosynthetic process'),
    gene('HGNC', 'APP', variants=hgvs('c.275341G>C')),
    gene('HGNC', 'APP'),
    pathology('MESHD', 'Alzheimer Disease'),
    complex_abundance([protein('HGNC', 'F3'), protein('HGNC', 'F7')]),
    protein('HGNC', 'F3'),
    protein('HGNC', 'F7'),
    protein('HGNC', 'F9'),
    protein('HGNC', 'GSK3B', variants=pmod('Ph', 'Ser', 9)),
    protein('HGNC', 'GSK3B'),
    pathology('MESHD', 'Psoriasis'),
    pathology('MESHD', 'Skin Diseases'),
    reaction(
        reactants=[
            abundance('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
            abundance('CHEBI', 'NADPH'),
            abundance('CHEBI', 'hydron')
        ],
        products=[
            abundance('CHEBI', 'NADP(+)'),
            abundance('CHEBI', 'mevalonate')
        ]
    ),
    abundance('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
    abundance('CHEBI', 'NADPH'),
    abundance('CHEBI', 'hydron'),
    abundance('CHEBI', 'mevalonate'),
    abundance('CHEBI', 'NADP(+)'),
    abundance('CHEBI', 'nitric oxide'),
    complex_abundance([
        protein('HGNC', 'ITGAV'),
        protein('HGNC', 'ITGB3')
    ]),
    protein('HGNC', 'ITGAV'),
    protein('HGNC', 'ITGB3'),
    protein('HGNC', 'FADD'),
    abundance('TESTNS2', 'Abeta_42'),
    protein('TESTNS2', 'GSK3 Family'),
    protein('HGNC', 'PRKCA'),
    protein('HGNC', 'CDK5'),
    protein('HGNC', 'CASP8'),
    protein('HGNC', 'AKT1', variants=pmod(namespace='TESTNS2', name='PhosRes', code='Ser', position=473)),
    protein('HGNC', 'HRAS', variants=pmod('Palm')),
    bioprocess('GO', 'apoptotic process'),
    composite_abundance([
        abundance('TESTNS2', 'Abeta_42'),
        protein('HGNC', 'CASP8'),
        protein('HGNC', 'FADD')
    ]),
    reaction(
        reactants=[protein('HGNC', 'CDK5R1')],
        products=[protein('HGNC', 'CDK5')],
    ),
    protein('HGNC', 'PRKCB'),
    named_complex_abundance('TESTNS2', 'AP-1 Complex'),
    protein('HGNC', 'PRKCE'),
    protein('HGNC', 'PRKCD'),
    protein('TESTNS2', 'CAPN Family'),
    gene('TESTNS2', 'AKT1 ortholog'),
    protein('HGNC', 'HRAS'),
    protein('HGNC', 'CDK5R1'),
    protein('TESTNS2', 'PRKC'),
    bioprocess('GO', 'neuron apoptotic process'),
    protein('HGNC', 'MAPT', variants=pmod('Ph')),
    protein('HGNC', 'MAPT'),
    gene('HGNC', 'ARRDC2'),
    gene('HGNC', 'ARRDC3'),
    gene('dbSNP', 'rs123456')
}

BEL_THOROUGH_EDGES = [
    (gene('HGNC', 'AKT1', variants=hgvs('p.Phe508del')), akt1, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: DIRECTLY_DECREASES,
    }),
    (akt1, protein('HGNC', 'AKT1', variants=pmod('Ph', 'Ser', 473)), {
        RELATION: HAS_VARIANT,
    }),
    (akt1, protein('HGNC', 'AKT1', variants=hgvs('p.C40*')), {
        RELATION: HAS_VARIANT,
    }),
    (akt1,
     protein('HGNC', 'AKT1', variants=[hgvs('p.Ala127Tyr'), pmod('Ph', 'Ser')]), {
         RELATION: HAS_VARIANT,
     }),
    (akt1,
     protein('HGNC', 'AKT1', variants=[hgvs('p.Ala127Tyr'), pmod('Ph', 'Ser')]), {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: DIRECTLY_DECREASES,
         SUBJECT: {LOCATION: {NAMESPACE: 'GO', NAME: 'intracellular'}},
         OBJECT: {LOCATION: {NAMESPACE: 'GO', NAME: 'intracellular'}},
     }),
    (akt1, protein('HGNC', 'AKT1', variants=hgvs('p.Arg1851*')), {
        RELATION: HAS_VARIANT,
    }),
    (akt1, protein('HGNC', 'AKT1', variants=hgvs('p.40*')), {
        RELATION: HAS_VARIANT,
    }),
    (akt1, protein('HGNC', 'MIA', variants=fragment()), {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        SUBJECT: {MODIFIER: DEGRADATION},
    }),
    (akt1, protein('HGNC', 'CFTR', variants=hgvs('p.Gly576Ala')), {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
    }),
    (akt1, rna('HGNC', 'CFTR', variants=hgvs('r.1521_1523delcuu')), {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        SUBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'kin'}},
    }),
    (akt1, rna('HGNC', 'CFTR', variants=hgvs('r.1653_1655delcuu')), {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        SUBJECT: {MODIFIER: ACTIVITY},
    }),
    (akt1, egfr, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        SUBJECT: {
            MODIFIER: ACTIVITY,
            EFFECT: {
                NAMESPACE: BEL_DEFAULT_NAMESPACE,
                NAME: 'cat'
            }
        },
        OBJECT: {MODIFIER: DEGRADATION},
    }),
    (akt1, egfr, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        SUBJECT: {
            MODIFIER: ACTIVITY,
            EFFECT: {NAME: 'kin', NAMESPACE: BEL_DEFAULT_NAMESPACE}
        },
        OBJECT: translocation(
            {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'intracellular'},
            {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'extracellular space'}
        ),
    }),
    (gene('HGNC', 'AKT1', variants=hgvs('c.308G>A')), tmprss2_erg_gene_fusion, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: CAUSES_NO_CHANGE,
    }),
    (gene('HGNC', 'AKT1', variants=hgvs('c.308G>A')),
     gene('HGNC', 'AKT1', variants=[hgvs('c.1521_1523delCTT'), hgvs('c.308G>A'), hgvs('p.Phe508del')]), {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
         SUBJECT: {LOCATION: {NAMESPACE: 'GO', NAME: 'intracellular'}},
     }),
    (mirna('HGNC', 'MIR21'), bcr_jak2_gene_fusion,
     {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: DIRECTLY_INCREASES,
     }),
    (mirna('HGNC', 'MIR21'), protein('HGNC', 'AKT1', variants=pmod('Ph', 'Ser', 473)),
     {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: DECREASES,
         SUBJECT: {LOCATION: {NAMESPACE: 'GO', NAME: 'intracellular'}},
     }),
    (mirna('HGNC', 'MIR21'), mirna('HGNC', 'MIR21', variants=hgvs('p.Phe508del')), {
        RELATION: HAS_VARIANT,
    }),
    (gene('HGNC', 'CFTR', variants=hgvs('c.1521_1523delCTT')), akt1,
     {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
         OBJECT: {MODIFIER: DEGRADATION},
     }),
    (gene('HGNC', 'CFTR'), gene('HGNC', 'CFTR', variants=hgvs('c.1521_1523delCTT')), {
        RELATION: HAS_VARIANT,
    }),
    (gene('HGNC', 'CFTR'), gene('HGNC', 'CFTR', variants=hgvs('g.117199646_117199648delCTT')), {
        RELATION: HAS_VARIANT,
    }),
    (gene('HGNC', 'CFTR'), gene('HGNC', 'CFTR', variants=hgvs('c.1521_1523delCTT')), {
        RELATION: HAS_VARIANT,
    }),
    (gene('HGNC', 'CFTR', variants=hgvs('g.117199646_117199648delCTT')),
     gene('HGNC', 'CFTR', variants=hgvs('c.1521_1523delCTT')), {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
     }),
    (mirna('HGNC', 'MIR21', variants=hgvs('p.Phe508del')), protein('HGNC', 'AKT1', variants=hgvs('p.C40*')),
     {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
         SUBJECT: {LOCATION: {NAMESPACE: 'GO', NAME: 'intracellular'}},
     }),
    (chchd4_aifm1_gene_fusion, tmprss2_erg_protein_fusion, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
    }),
    (protein('HGNC', 'AKT1', variants=hgvs('p.Arg1851*')), bcr_jak2_protein_fusion, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
    }),
    (protein('HGNC', 'AKT1', variants=hgvs('p.40*')), chchd4_aifm1_protein_fusion,
     {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
     }),
    (protein('HGNC', 'CFTR', variants=hgvs_reference()), egfr, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        OBJECT: translocation(INTRACELLULAR, CELL_SURFACE),
    }),
    (cftr, protein('HGNC', 'CFTR', variants=hgvs('=')), {
        RELATION: HAS_VARIANT,
    }),
    (cftr, protein('HGNC', 'CFTR', variants=hgvs('?')), {
        RELATION: HAS_VARIANT,
    }),
    (cftr, protein('HGNC', 'CFTR', variants=hgvs('p.Phe508del')), {
        RELATION: HAS_VARIANT,
    }),
    (cftr, protein('HGNC', 'CFTR', variants=hgvs('p.Gly576Ala')), {
        RELATION: HAS_VARIANT,
    }),
    (mia, protein('HGNC', 'MIA', variants=fragment(5, 20)), {
        RELATION: HAS_VARIANT,
    }),
    (mia, protein('HGNC', 'MIA', variants=fragment(1, '?')), {
        RELATION: HAS_VARIANT,
    }),
    (mia, protein('HGNC', 'MIA', variants=fragment()), {
        RELATION: HAS_VARIANT,
    }),
    (mia, protein('HGNC', 'MIA', variants=fragment(description='55kD')), {
        RELATION: HAS_VARIANT,
    }),
    (akt1_rna, rna('HGNC', 'AKT1', variants=[hgvs('c.1521_1523delCTT'), hgvs('p.Phe508del')]), {
        RELATION: HAS_VARIANT,
    }),
    (akt1_rna, akt1, {
        RELATION: TRANSLATED_TO,
    }),
    (gene('HGNC', 'APP'), gene('HGNC', 'APP', variants=hgvs('c.275341G>C')), {
        RELATION: HAS_VARIANT,
    }),
    (complex_abundance([protein('HGNC', 'F3'), protein('HGNC', 'F7')]), protein('HGNC', 'F3'), {
        RELATION: HAS_COMPONENT,
    }),
    (complex_abundance([protein('HGNC', 'F3'), protein('HGNC', 'F7')]), protein('HGNC', 'F7'), {
        RELATION: HAS_COMPONENT,
    }),
    (protein('HGNC', 'GSK3B'), protein('HGNC', 'GSK3B', variants=pmod('Ph', 'Ser', 9)), {
        RELATION: HAS_VARIANT,
    }),
    (pathology('MESHD', 'Psoriasis'), pathology('MESHD', 'Skin Diseases'), {
        RELATION: IS_A,
    }),

    (complex_abundance([gene('HGNC', 'NCF1'), protein('HGNC', 'HBP1')]), protein('HGNC', 'HBP1'), {
        RELATION: HAS_COMPONENT,
    }),
    (complex_abundance([gene('HGNC', 'NCF1'), protein('HGNC', 'HBP1')]), gene('HGNC', 'NCF1'), {
        RELATION: HAS_COMPONENT,
    }),

    (complex_abundance([protein('HGNC', 'FOS'), protein('HGNC', 'JUN')]), protein('HGNC', 'FOS'), {
        RELATION: HAS_COMPONENT,
    }),
    (complex_abundance([protein('HGNC', 'FOS'), protein('HGNC', 'JUN')]), protein('HGNC', 'JUN'), {
        RELATION: HAS_COMPONENT,
    }),
    (rna('HGNC', 'CFTR'), rna('HGNC', 'CFTR', variants=hgvs('r.1521_1523delcuu')), {
        RELATION: HAS_VARIANT,
    }),
    (rna('HGNC', 'CFTR'), rna('HGNC', 'CFTR', variants=hgvs('r.1653_1655delcuu')), {
        RELATION: HAS_VARIANT,
    }),
    (composite_abundance([interleukin_23_complex, il6]), il6, {
        RELATION: HAS_COMPONENT,
    }),
    (composite_abundance([interleukin_23_complex, il6]), interleukin_23_complex, {
        RELATION: HAS_COMPONENT,
    }),
    (protein('HGNC', 'CFTR', variants=hgvs('?')), pathology('MESHD', 'Adenocarcinoma'), {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
    }),
    (rna('HGNC', 'AKT1', variants=[hgvs('c.1521_1523delCTT'), hgvs('p.Phe508del')]),
     tmprss2_erg_rna_fusion, {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: DIRECTLY_INCREASES,
     }),
    (rna_fusion(rna('HGNC', 'TMPRSS2'), rna('HGNC', 'ERG')),
     complex_abundance([gene('HGNC', 'NCF1'), protein('HGNC', 'HBP1')]), {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
     }),
    (protein('HGNC', 'MIA', variants=fragment(5, 20)), named_complex_abundance('GO', 'interleukin-23 complex'), {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        OBJECT: secretion(),
    }),
    (protein('HGNC', 'MIA', variants=fragment(1, '?')), egfr, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        OBJECT: {
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
        OBJECT: {
            MODIFIER: TRANSLOCATION, EFFECT: {
                FROM_LOC: {NAMESPACE: 'GO', NAME: 'cell surface'},
                TO_LOC: {NAMESPACE: 'GO', NAME: 'endosome'}
            }
        },
    }),
    (rna_fusion(rna('HGNC', 'CHCHD4'), rna('HGNC', 'AIFM1'), ),
     complex_abundance([protein('HGNC', 'FOS'), protein('HGNC', 'JUN')]),
     {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
     }),
    (composite_abundance([interleukin_23_complex, il6]),
     bioprocess('GO', 'cell cycle arrest'), {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: DECREASES,
     }),
    (protein('HGNC', 'CAT'), hydrogen_peroxide, {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: DIRECTLY_DECREASES,
        SUBJECT: {LOCATION: {NAMESPACE: 'GO', NAME: 'intracellular'}},
    }),
    (gene('HGNC', 'CAT'), hydrogen_peroxide, {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: DIRECTLY_DECREASES,
        SUBJECT: {LOCATION: {NAMESPACE: 'GO', NAME: 'intracellular'}},
    }),
    (protein('HGNC', 'HMGCR'), bioprocess('GO', 'cholesterol biosynthetic process'), {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: RATE_LIMITING_STEP_OF,
        SUBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'cat'}},
    }),
    (gene('HGNC', 'APP', variants=hgvs('c.275341G>C')), pathology('MESHD', 'Alzheimer Disease'),
     {
         EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
         CITATION: citation_2,
         RELATION: CAUSES_NO_CHANGE,
     }),

    (complex_abundance([protein('HGNC', 'F3'), protein('HGNC', 'F7')]), protein('HGNC', 'F9'), {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: REGULATES,
        SUBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAME: 'pep', NAMESPACE: BEL_DEFAULT_NAMESPACE}},
        OBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAME: 'pep', NAMESPACE: BEL_DEFAULT_NAMESPACE}},
    }),
    (protein('HGNC', 'GSK3B', variants=pmod('Ph', 'Ser', 9)), protein('HGNC', 'GSK3B'), {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: POSITIVE_CORRELATION,
        OBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'kin'}},
    }),

    (protein('HGNC', 'GSK3B'), protein('HGNC', 'GSK3B', variants=pmod('Ph', 'Ser', 9)), {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: POSITIVE_CORRELATION,
        SUBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'kin'}},
    }),

    (reaction(
        reactants=(
            abundance('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
            abundance('CHEBI', 'NADPH'),
            abundance('CHEBI', 'hydron')
        ),
        products=(
            abundance('CHEBI', 'NADP(+)'),
            abundance('CHEBI', 'mevalonate')
        )
    ),
     abundance('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'), {
         RELATION: HAS_REACTANT,
     }),
    (reaction(
        reactants=(
            abundance('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
            abundance('CHEBI', 'NADPH'),
            abundance('CHEBI', 'hydron')
        ),
        products=(
            abundance('CHEBI', 'NADP(+)'),
            abundance('CHEBI', 'mevalonate')
        )
    ),
     abundance('CHEBI', 'NADPH'), {
         RELATION: HAS_REACTANT,
     }),
    (
        reaction(
            reactants=(
                abundance('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
                abundance('CHEBI', 'NADPH'),
                abundance('CHEBI', 'hydron')
            ),
            products=(
                abundance('CHEBI', 'NADP(+)'),
                abundance('CHEBI', 'mevalonate')
            )
        ),
        abundance('CHEBI', 'hydron'), {
            RELATION: HAS_REACTANT,
        }),
    (reaction(
        reactants=(
            abundance('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
            abundance('CHEBI', 'NADPH'),
            abundance('CHEBI', 'hydron')
        ),
        products=(
            abundance('CHEBI', 'NADP(+)'),
            abundance('CHEBI', 'mevalonate'))
    ),
     abundance('CHEBI', 'mevalonate'), {
         RELATION: HAS_PRODUCT,
     }),
    (reaction(
        reactants=(
            abundance('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
            abundance('CHEBI', 'NADPH'),
            abundance('CHEBI', 'hydron')
        ),
        products=(
            abundance('CHEBI', 'NADP(+)'),
            abundance('CHEBI', 'mevalonate')
        )
    ),
     abundance('CHEBI', 'NADP(+)'), {
         RELATION: HAS_PRODUCT,
     }),
    (reaction(
        reactants=(
            abundance('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
            abundance('CHEBI', 'NADPH'),
            abundance('CHEBI', 'hydron')
        ),
        products=(
            abundance('CHEBI', 'NADP(+)'),
            abundance('CHEBI', 'mevalonate')
        )
    ),
     bioprocess('GO', 'cholesterol biosynthetic process'),
     {
         EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
         CITATION: citation_2,
         RELATION: SUBPROCESS_OF,
     }),
    (abundance('CHEBI', 'nitric oxide'),
     complex_abundance([protein('HGNC', 'ITGAV'), protein('HGNC', 'ITGB3')]), {
         EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
         CITATION: citation_2,
         RELATION: INCREASES,
         OBJECT: {
             MODIFIER: TRANSLOCATION,
             EFFECT: {
                 FROM_LOC: {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'intracellular'},
                 TO_LOC: {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'cell surface'}
             }
         },
     }),
    (complex_abundance([protein('HGNC', 'ITGAV'), protein('HGNC', 'ITGB3')]), protein('HGNC', 'ITGAV'), {
        RELATION: HAS_COMPONENT,
    }),
    (complex_abundance([protein('HGNC', 'ITGAV'), protein('HGNC', 'ITGB3')]), protein('HGNC', 'ITGB3'), {
        RELATION: HAS_COMPONENT,
    }),
    (gene('HGNC', 'ARRDC2'), gene('HGNC', 'ARRDC3'), {
        RELATION: EQUIVALENT_TO,
    }),
    (gene('HGNC', 'ARRDC3'), gene('HGNC', 'ARRDC2'), {
        RELATION: EQUIVALENT_TO,
        CITATION: citation_2,
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification'
    }),
    (gene('dbSNP', 'rs123456'), gene('HGNC', 'CFTR', variants=hgvs('c.1521_1523delCTT')), {
        RELATION: ASSOCIATION,
        CITATION: citation_2,
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification'
    }),
    (gene('HGNC', 'CFTR', variants=hgvs('c.1521_1523delCTT')), gene('dbSNP', 'rs123456'), {
        RELATION: ASSOCIATION,
        CITATION: citation_2,
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification'
    }),
]
