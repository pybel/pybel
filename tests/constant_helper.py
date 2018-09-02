# -*- coding: utf-8 -*-

"""Constants for PyBEL tests."""

import logging

from pybel.constants import (
    ABUNDANCE, ACTIVITY, ANNOTATIONS, ASSOCIATION, BEL_DEFAULT_NAMESPACE, BIOPROCESS, CAUSES_NO_CHANGE, CITATION,
    CITATION_NAME, CITATION_REFERENCE, CITATION_TYPE, COMPLEX, COMPOSITE, DECREASES, DEGRADATION, DIRECTLY_DECREASES,
    DIRECTLY_INCREASES, EFFECT, EQUIVALENT_TO, EVIDENCE, FRAGMENT, FROM_LOC, GENE, GMOD,
    HAS_COMPONENT, HAS_PRODUCT, HAS_REACTANT, HAS_VARIANT, HGVS, INCREASES, IS_A, LOCATION, METADATA_AUTHORS,
    METADATA_CONTACT, METADATA_COPYRIGHT, METADATA_DESCRIPTION, METADATA_LICENSES, METADATA_NAME, METADATA_PROJECT,
    METADATA_VERSION, MIRNA, MODIFIER, NAME, NAMESPACE, OBJECT, PATHOLOGY, PMOD, POSITIVE_CORRELATION, PROTEIN,
    RATE_LIMITING_STEP_OF, REACTION,
    REGULATES, RELATION, RNA, SUBJECT, SUBPROCESS_OF, TO_LOC, TRANSCRIBED_TO, TRANSLATED_TO, TRANSLOCATION,
)
from pybel.dsl import translocation

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

AKT1 = (PROTEIN, 'HGNC', 'AKT1')
EGFR = (PROTEIN, 'HGNC', 'EGFR')
FADD = (PROTEIN, 'HGNC', 'FADD')
CASP8 = (PROTEIN, 'HGNC', 'CASP8')
cftr = (PROTEIN, 'HGNC', 'CFTR')
mia = (PROTEIN, 'HGNC', 'MIA')

akt1_gene = (GENE, 'HGNC', 'AKT1')
akt1_rna = (RNA, 'HGNC', 'AKT1')
oxygen_atom = (ABUNDANCE, 'CHEBI', 'oxygen atom')

BEL_THOROUGH_NODES = {
    oxygen_atom,
    (GENE, 'HGNC', 'AKT1', (GMOD, (BEL_DEFAULT_NAMESPACE, 'Me'))),
    akt1_gene,
    (GENE, 'HGNC', 'AKT1', (HGVS, 'p.Phe508del')),
    AKT1,
    (GENE, 'HGNC', 'AKT1', (HGVS, 'c.308G>A')),
    (GENE, ('HGNC', 'TMPRSS2'), ('c', 1, 79), ('HGNC', 'ERG'), ('c', 312, 5034)),
    (GENE, 'HGNC', 'AKT1', (HGVS, 'c.1521_1523delCTT'), (HGVS, 'c.308G>A'), (HGVS, 'p.Phe508del')),
    (MIRNA, 'HGNC', 'MIR21'),
    (GENE, ('HGNC', 'BCR'), ('c', '?', 1875), ('HGNC', 'JAK2'), ('c', 2626, '?')),
    (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')),
    (GENE, 'HGNC', 'CFTR'),
    (GENE, 'HGNC', 'CFTR', (HGVS, 'g.117199646_117199648delCTT')),
    (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')),
    (PROTEIN, 'HGNC', 'AKT1', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 473)),
    (MIRNA, 'HGNC', 'MIR21', (HGVS, 'p.Phe508del')),
    (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.C40*')),
    (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Ala127Tyr'), (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser')),
    (GENE, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
    (PROTEIN, ('HGNC', 'TMPRSS2'), ('p', 1, 79), ('HGNC', 'ERG'), ('p', 312, 5034)),
    (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Arg1851*')),
    (PROTEIN, ('HGNC', 'BCR'), ('p', '?', 1875), ('HGNC', 'JAK2'), ('p', 2626, '?')),
    (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.40*')),
    (PROTEIN, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
    (PROTEIN, 'HGNC', 'CFTR', (HGVS, '=')),
    cftr,
    EGFR,
    (PROTEIN, 'HGNC', 'CFTR', (HGVS, '?')),
    (PATHOLOGY, 'MESHD', 'Adenocarcinoma'),
    (PROTEIN, 'HGNC', 'CFTR', (HGVS, 'p.Phe508del')),
    (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, (5, 20))),
    mia,
    (COMPLEX, 'GOCC', 'interleukin-23 complex'),
    (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, (1, '?'))),
    (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, '?')),
    (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, '?', '55kD')),
    (PROTEIN, 'HGNC', 'CFTR', (HGVS, 'p.Gly576Ala')),
    akt1_rna,
    (RNA, 'HGNC', 'AKT1', (HGVS, 'c.1521_1523delCTT'), (HGVS, 'p.Phe508del')),
    (RNA, ('HGNC', 'TMPRSS2'), ('r', 1, 79), ('HGNC', 'ERG'), ('r', 312, 5034)),
    (RNA, ('HGNC', 'TMPRSS2'), ('?',), ('HGNC', 'ERG'), ('?',)),
    (COMPLEX, (GENE, 'HGNC', 'NCF1'), (PROTEIN, 'HGNC', 'HBP1')),
    (PROTEIN, 'HGNC', 'HBP1'),
    (GENE, 'HGNC', 'NCF1'),
    (RNA, ('HGNC', 'BCR'), ('r', '?', 1875), ('HGNC', 'JAK2'), ('r', 2626, '?')),
    (RNA, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
    (COMPLEX, (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')),
    (PROTEIN, 'HGNC', 'FOS'),
    (PROTEIN, 'HGNC', 'JUN'),
    (RNA, 'HGNC', 'CFTR', (HGVS, 'r.1521_1523delcuu')),
    (RNA, 'HGNC', 'CFTR'),
    (RNA, 'HGNC', 'CFTR', (HGVS, 'r.1653_1655delcuu')),
    (COMPOSITE, (COMPLEX, 'GOCC', 'interleukin-23 complex'), (PROTEIN, 'HGNC', 'IL6')),
    (PROTEIN, 'HGNC', 'IL6'),
    (BIOPROCESS, 'GOBP', 'cell cycle arrest'),
    (ABUNDANCE, 'CHEBI', 'hydrogen peroxide'),
    (PROTEIN, 'HGNC', 'CAT'),
    (GENE, 'HGNC', 'CAT'),
    (PROTEIN, 'HGNC', 'HMGCR'),
    (BIOPROCESS, 'GOBP', 'cholesterol biosynthetic process'),
    (GENE, 'HGNC', 'APP', (HGVS, 'c.275341G>C')),
    (GENE, 'HGNC', 'APP'),
    (PATHOLOGY, 'MESHD', 'Alzheimer Disease'),
    (COMPLEX, (PROTEIN, 'HGNC', 'F3'), (PROTEIN, 'HGNC', 'F7')),
    (PROTEIN, 'HGNC', 'F3'),
    (PROTEIN, 'HGNC', 'F7'),
    (PROTEIN, 'HGNC', 'F9'),
    (PROTEIN, 'HGNC', 'GSK3B', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 9)),
    (PROTEIN, 'HGNC', 'GSK3B'),
    (PATHOLOGY, 'MESHD', 'Psoriasis'),
    (PATHOLOGY, 'MESHD', 'Skin Diseases'),
    (
        REACTION,
        (
            (ABUNDANCE, 'CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
            (ABUNDANCE, 'CHEBI', 'NADPH'),
            (ABUNDANCE, 'CHEBI', 'hydron')
        ),
        (
            (ABUNDANCE, 'CHEBI', 'NADP(+)'),
            (ABUNDANCE, 'CHEBI', 'mevalonate')
        )
    ),
    (ABUNDANCE, 'CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
    (ABUNDANCE, 'CHEBI', 'NADPH'),
    (ABUNDANCE, 'CHEBI', 'hydron'),
    (ABUNDANCE, 'CHEBI', 'mevalonate'),
    (ABUNDANCE, 'CHEBI', 'NADP(+)'),
    (ABUNDANCE, 'CHEBI', 'nitric oxide'),
    (COMPLEX, (PROTEIN, 'HGNC', 'ITGAV'), (PROTEIN, 'HGNC', 'ITGB3')),
    (PROTEIN, 'HGNC', 'ITGAV'),
    (PROTEIN, 'HGNC', 'ITGB3'),
    (PROTEIN, 'HGNC', 'FADD'),
    (ABUNDANCE, 'TESTNS2', 'Abeta_42'),
    (PROTEIN, 'TESTNS2', 'GSK3 Family'),
    (PROTEIN, 'HGNC', 'PRKCA'),
    (PROTEIN, 'HGNC', 'CDK5'),
    (PROTEIN, 'HGNC', 'CASP8'),
    (PROTEIN, 'HGNC', 'AKT1', (PMOD, ('TESTNS2', 'PhosRes'), 'Ser', 473)),
    (PROTEIN, 'HGNC', 'HRAS', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Palm'))),
    (BIOPROCESS, 'GOBP', 'apoptotic process'),
    (COMPOSITE, (ABUNDANCE, 'TESTNS2', 'Abeta_42'), (PROTEIN, 'HGNC', 'CASP8'),
     (PROTEIN, 'HGNC', 'FADD')),
    (
        REACTION,
        (
            (PROTEIN, 'HGNC', 'CDK5R1'),
        ),
        (
            (PROTEIN, 'HGNC', 'CDK5'),
        )
    ),
    (PROTEIN, 'HGNC', 'PRKCB'),
    (COMPLEX, 'TESTNS2', 'AP-1 Complex'),
    (PROTEIN, 'HGNC', 'PRKCE'),
    (PROTEIN, 'HGNC', 'PRKCD'),
    (PROTEIN, 'TESTNS2', 'CAPN Family'),
    (GENE, 'TESTNS2', 'AKT1 ortholog'),
    (PROTEIN, 'HGNC', 'HRAS'),
    (PROTEIN, 'HGNC', 'CDK5R1'),
    (PROTEIN, 'TESTNS2', 'PRKC'),
    (BIOPROCESS, 'GOBP', 'neuron apoptotic process'),
    (PROTEIN, 'HGNC', 'MAPT', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'))),
    (PROTEIN, 'HGNC', 'MAPT'),
    (GENE, 'HGNC', 'ARRDC2'),
    (GENE, 'HGNC', 'ARRDC3'),
    (GENE, 'dbSNP', 'rs123456')
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

BEL_THOROUGH_EDGES = [
    (oxygen_atom, (GENE, 'HGNC', 'AKT1', (GMOD, (BEL_DEFAULT_NAMESPACE, 'Me'))), {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        ANNOTATIONS: {
            'TESTAN1': {'1': True, '2': True},
            'TestRegex': {'9000': True}
        }
    }),
    (akt1_gene, (GENE, 'HGNC', 'AKT1', (GMOD, (BEL_DEFAULT_NAMESPACE, 'Me'))), {
        RELATION: HAS_VARIANT,
    }),
    (akt1_gene, oxygen_atom, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: DECREASES, SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
        OBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
    }),
    (akt1_gene, (GENE, 'HGNC', 'AKT1', (HGVS, 'p.Phe508del')), {
        RELATION: HAS_VARIANT,
    }),
    (akt1_gene, (GENE, 'HGNC', 'AKT1', (HGVS, 'c.308G>A')), {
        RELATION: HAS_VARIANT,
    }),
    (akt1_gene,
     (GENE, 'HGNC', 'AKT1', (HGVS, 'c.1521_1523delCTT'), (HGVS, 'c.308G>A'), (HGVS, 'p.Phe508del')), {
         RELATION: HAS_VARIANT,
     }),
    (akt1_gene, akt1_rna, {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: TRANSCRIBED_TO,
    }),
    ((GENE, 'HGNC', 'AKT1', (HGVS, 'p.Phe508del')), AKT1, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: DIRECTLY_DECREASES,
    }),
    (AKT1, (PROTEIN, 'HGNC', 'AKT1', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 473)), {
        RELATION: HAS_VARIANT,
    }),
    (AKT1, (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.C40*')), {
        RELATION: HAS_VARIANT,
    }),
    (AKT1,
     (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Ala127Tyr'), (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser')), {
         RELATION: HAS_VARIANT,
     }),
    (AKT1,
     (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Ala127Tyr'), (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser')), {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: DIRECTLY_DECREASES,
         SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
         OBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
     }),
    (AKT1, (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Arg1851*')), {
        RELATION: HAS_VARIANT,
    }),
    (AKT1, (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.40*')), {
        RELATION: HAS_VARIANT,
    }),
    (AKT1, (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, '?')), {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        SUBJECT: {MODIFIER: DEGRADATION},
    }),
    (AKT1, (PROTEIN, 'HGNC', 'CFTR', (HGVS, 'p.Gly576Ala')), {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
    }),
    (AKT1, (RNA, 'HGNC', 'CFTR', (HGVS, 'r.1521_1523delcuu')), {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        SUBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'kin'}},
    }),
    (AKT1, (RNA, 'HGNC', 'CFTR', (HGVS, 'r.1653_1655delcuu')), {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        SUBJECT: {MODIFIER: ACTIVITY},
    }),
    (AKT1, EGFR, {
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
    (AKT1, EGFR, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        SUBJECT: {
            MODIFIER: ACTIVITY,
            EFFECT: {NAME: 'kin', NAMESPACE: BEL_DEFAULT_NAMESPACE}
        },
        OBJECT: translocation(
            {NAMESPACE: 'GOCC', NAME: 'intracellular'},
            {NAMESPACE: 'GOCC', NAME: 'extracellular space'}
        ),
    }),
    ((GENE, 'HGNC', 'AKT1', (HGVS, 'c.308G>A')),
     (GENE, ('HGNC', 'TMPRSS2'), ('c', 1, 79), ('HGNC', 'ERG'), ('c', 312, 5034)), {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: CAUSES_NO_CHANGE,
     }),
    ((GENE, 'HGNC', 'AKT1', (HGVS, 'c.308G>A')),
     (GENE, 'HGNC', 'AKT1', (HGVS, 'c.1521_1523delCTT'), (HGVS, 'c.308G>A'), (HGVS, 'p.Phe508del')), {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
         SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
     }),
    ((MIRNA, 'HGNC', 'MIR21'),
     (GENE, ('HGNC', 'BCR'), ('c', '?', 1875), ('HGNC', 'JAK2'), ('c', 2626, '?')),
     {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: DIRECTLY_INCREASES,
     }),
    ((MIRNA, 'HGNC', 'MIR21'), (PROTEIN, 'HGNC', 'AKT1', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 473)),
     {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: DECREASES,
         SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
     }),
    ((MIRNA, 'HGNC', 'MIR21'), (MIRNA, 'HGNC', 'MIR21', (HGVS, 'p.Phe508del')), {
        RELATION: HAS_VARIANT,
    }),
    ((GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')), AKT1,
     {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
         OBJECT: {MODIFIER: DEGRADATION},
     }),
    ((GENE, 'HGNC', 'CFTR'), (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')), {
        RELATION: HAS_VARIANT,
    }),
    ((GENE, 'HGNC', 'CFTR'), (GENE, 'HGNC', 'CFTR', (HGVS, 'g.117199646_117199648delCTT')), {
        RELATION: HAS_VARIANT,
    }),
    ((GENE, 'HGNC', 'CFTR'), (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')), {
        RELATION: HAS_VARIANT,
    }),
    ((GENE, 'HGNC', 'CFTR', (HGVS, 'g.117199646_117199648delCTT')),
     (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')), {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
     }),
    ((MIRNA, 'HGNC', 'MIR21', (HGVS, 'p.Phe508del')), (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.C40*')),
     {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
         SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
     }),
    ((GENE, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
     (PROTEIN, ('HGNC', 'TMPRSS2'), ('p', 1, 79), ('HGNC', 'ERG'), ('p', 312, 5034)), {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
     }),
    ((PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Arg1851*')),
     (PROTEIN, ('HGNC', 'BCR'), ('p', '?', 1875), ('HGNC', 'JAK2'), ('p', 2626, '?')), {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
     }),
    ((PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.40*')),
     (PROTEIN, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
     {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
     }),
    ((PROTEIN, 'HGNC', 'CFTR', (HGVS, '=')), EGFR, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        OBJECT: {
            MODIFIER: TRANSLOCATION,
            EFFECT: {
                FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'intracellular'},
                TO_LOC: {NAMESPACE: 'GOCC', NAME: 'cell surface'}
            }
        },
    }),
    (cftr, (PROTEIN, 'HGNC', 'CFTR', (HGVS, '=')), {
        RELATION: HAS_VARIANT,
    }),
    (cftr, (PROTEIN, 'HGNC', 'CFTR', (HGVS, '?')), {
        RELATION: HAS_VARIANT,
    }),
    (cftr, (PROTEIN, 'HGNC', 'CFTR', (HGVS, 'p.Phe508del')), {
        RELATION: HAS_VARIANT,
    }),
    (cftr, (PROTEIN, 'HGNC', 'CFTR', (HGVS, 'p.Gly576Ala')), {
        RELATION: HAS_VARIANT,
    }),
    ((PROTEIN, 'HGNC', 'CFTR', (HGVS, '?')), (PATHOLOGY, 'MESHD', 'Adenocarcinoma'), {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
    }),
    ((PROTEIN, 'HGNC', 'MIA', (FRAGMENT, (5, 20))), (COMPLEX, 'GOCC', 'interleukin-23 complex'), {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        OBJECT: {
            MODIFIER: TRANSLOCATION,
            EFFECT: {
                FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'intracellular'},
                TO_LOC: {NAMESPACE: 'GOCC', NAME: 'extracellular space'}
            }
        },
    }),
    (mia, (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, (5, 20))), {
        RELATION: HAS_VARIANT,
    }),
    (mia, (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, (1, '?'))), {
        RELATION: HAS_VARIANT,
    }),
    (mia, (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, '?')), {
        RELATION: HAS_VARIANT,
    }),
    (mia, (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, '?', '55kD')), {
        RELATION: HAS_VARIANT,
    }),
    ((PROTEIN, 'HGNC', 'MIA', (FRAGMENT, (1, '?'))), EGFR, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        OBJECT: {
            MODIFIER: TRANSLOCATION,
            EFFECT: {
                FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'cell surface'},
                TO_LOC: {NAMESPACE: 'GOCC', NAME: 'endosome'}
            }
        },
    }),
    (akt1_rna, EGFR, {
        EVIDENCE: dummy_evidence,
        CITATION: citation_1,
        RELATION: INCREASES,
        OBJECT: {
            MODIFIER: TRANSLOCATION, EFFECT: {
                FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'cell surface'},
                TO_LOC: {NAMESPACE: 'GOCC', NAME: 'endosome'}
            }
        },
    }),
    (akt1_rna, (RNA, 'HGNC', 'AKT1', (HGVS, 'c.1521_1523delCTT'), (HGVS, 'p.Phe508del')), {
        RELATION: HAS_VARIANT,
    }),
    (akt1_rna, AKT1, {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: TRANSLATED_TO,
    }),
    ((RNA, 'HGNC', 'AKT1', (HGVS, 'c.1521_1523delCTT'), (HGVS, 'p.Phe508del')),
     (RNA, ('HGNC', 'TMPRSS2'), ('r', 1, 79), ('HGNC', 'ERG'), ('r', 312, 5034)), {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: DIRECTLY_INCREASES,
     }),
    ((RNA, ('HGNC', 'TMPRSS2'), ('?',), ('HGNC', 'ERG'), ('?',)),
     (COMPLEX, (GENE, 'HGNC', 'NCF1'), (PROTEIN, 'HGNC', 'HBP1')), {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
     }),
    ((COMPLEX, (GENE, 'HGNC', 'NCF1'), (PROTEIN, 'HGNC', 'HBP1')), (PROTEIN, 'HGNC', 'HBP1'), {
        RELATION: HAS_COMPONENT,
    }),
    ((COMPLEX, (GENE, 'HGNC', 'NCF1'), (PROTEIN, 'HGNC', 'HBP1')), (GENE, 'HGNC', 'NCF1'), {
        RELATION: HAS_COMPONENT,
    }),
    ((RNA, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
     (COMPLEX, (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')),
     {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: INCREASES,
     }),
    ((COMPLEX, (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')), (PROTEIN, 'HGNC', 'FOS'), {
        RELATION: HAS_COMPONENT,
    }),
    ((COMPLEX, (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')), (PROTEIN, 'HGNC', 'JUN'), {
        RELATION: HAS_COMPONENT,
    }),
    ((RNA, 'HGNC', 'CFTR'), (RNA, 'HGNC', 'CFTR', (HGVS, 'r.1521_1523delcuu')), {
        RELATION: HAS_VARIANT,
    }),
    ((RNA, 'HGNC', 'CFTR'), (RNA, 'HGNC', 'CFTR', (HGVS, 'r.1653_1655delcuu')), {
        RELATION: HAS_VARIANT,
    }),
    ((COMPOSITE, (COMPLEX, 'GOCC', 'interleukin-23 complex'), (PROTEIN, 'HGNC', 'IL6')), (PROTEIN, 'HGNC', 'IL6'), {
        RELATION: HAS_COMPONENT,
    }),
    ((COMPOSITE, (COMPLEX, 'GOCC', 'interleukin-23 complex'), (PROTEIN, 'HGNC', 'IL6')),
     (COMPLEX, 'GOCC', 'interleukin-23 complex'), {
         RELATION: HAS_COMPONENT,
     }),
    ((COMPOSITE, (COMPLEX, 'GOCC', 'interleukin-23 complex'), (PROTEIN, 'HGNC', 'IL6')),
     (BIOPROCESS, 'GOBP', 'cell cycle arrest'), {
         EVIDENCE: dummy_evidence,
         CITATION: citation_1,
         RELATION: DECREASES,
     }),
    ((PROTEIN, 'HGNC', 'CAT'), (ABUNDANCE, 'CHEBI', 'hydrogen peroxide'), {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: DIRECTLY_DECREASES,
        SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
    }),
    ((GENE, 'HGNC', 'CAT'), (ABUNDANCE, 'CHEBI', 'hydrogen peroxide'), {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: DIRECTLY_DECREASES,
        SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
    }),
    ((PROTEIN, 'HGNC', 'HMGCR'), (BIOPROCESS, 'GOBP', 'cholesterol biosynthetic process'), {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: RATE_LIMITING_STEP_OF,
        SUBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'cat'}},
    }),
    ((GENE, 'HGNC', 'APP', (HGVS, 'c.275341G>C')), (PATHOLOGY, 'MESHD', 'Alzheimer Disease'),
     {
         EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
         CITATION: citation_2,
         RELATION: CAUSES_NO_CHANGE,
     }),
    ((GENE, 'HGNC', 'APP'), (GENE, 'HGNC', 'APP', (HGVS, 'c.275341G>C')), {
        RELATION: HAS_VARIANT,
    }),
    ((COMPLEX, (PROTEIN, 'HGNC', 'F3'), (PROTEIN, 'HGNC', 'F7')), (PROTEIN, 'HGNC', 'F3'), {
        RELATION: HAS_COMPONENT,
    }),
    ((COMPLEX, (PROTEIN, 'HGNC', 'F3'), (PROTEIN, 'HGNC', 'F7')), (PROTEIN, 'HGNC', 'F7'), {
        RELATION: HAS_COMPONENT,
    }),
    ((COMPLEX, (PROTEIN, 'HGNC', 'F3'), (PROTEIN, 'HGNC', 'F7')), (PROTEIN, 'HGNC', 'F9'), {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: REGULATES,
        SUBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAME: 'pep', NAMESPACE: BEL_DEFAULT_NAMESPACE}},
        OBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAME: 'pep', NAMESPACE: BEL_DEFAULT_NAMESPACE}},
    }),
    ((PROTEIN, 'HGNC', 'GSK3B', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 9)), (PROTEIN, 'HGNC', 'GSK3B'), {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: POSITIVE_CORRELATION,
        OBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'kin'}},
    }),
    ((PROTEIN, 'HGNC', 'GSK3B'), (PROTEIN, 'HGNC', 'GSK3B', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 9)), {
        RELATION: HAS_VARIANT,
    }),
    ((PROTEIN, 'HGNC', 'GSK3B'), (PROTEIN, 'HGNC', 'GSK3B', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 9)), {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: POSITIVE_CORRELATION,
        SUBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'kin'}},
    }),
    ((PATHOLOGY, 'MESHD', 'Psoriasis'), (PATHOLOGY, 'MESHD', 'Skin Diseases'), {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: IS_A,
    }),
    ((
         REACTION,
         (
             (ABUNDANCE, 'CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
             (ABUNDANCE, 'CHEBI', 'NADPH'),
             (ABUNDANCE, 'CHEBI', 'hydron')
         ),
         (
             (ABUNDANCE, 'CHEBI', 'NADP(+)'),
             (ABUNDANCE, 'CHEBI', 'mevalonate')
         )
     ),
     (ABUNDANCE, 'CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'), {
         RELATION: HAS_REACTANT,
     }),
    ((
         REACTION,
         (
             (ABUNDANCE, 'CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
             (ABUNDANCE, 'CHEBI', 'NADPH'),
             (ABUNDANCE, 'CHEBI', 'hydron')
         ),
         (
             (ABUNDANCE, 'CHEBI', 'NADP(+)'),
             (ABUNDANCE, 'CHEBI', 'mevalonate')
         )
     ),
     (ABUNDANCE, 'CHEBI', 'NADPH'), {
         RELATION: HAS_REACTANT,
     }),
    ((
         REACTION,
         (
             (ABUNDANCE, 'CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
             (ABUNDANCE, 'CHEBI', 'NADPH'),
             (ABUNDANCE, 'CHEBI', 'hydron')
         ),
         (
             (ABUNDANCE, 'CHEBI', 'NADP(+)'),
             (ABUNDANCE, 'CHEBI', 'mevalonate')
         )
     ),
     (ABUNDANCE, 'CHEBI', 'hydron'), {
         RELATION: HAS_REACTANT,
     }),
    ((
         REACTION,
         (
             (ABUNDANCE, 'CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
             (ABUNDANCE, 'CHEBI', 'NADPH'),
             (ABUNDANCE, 'CHEBI', 'hydron')
         ),
         (
             (ABUNDANCE, 'CHEBI', 'NADP(+)'),
             (ABUNDANCE, 'CHEBI', 'mevalonate'))
     ),
     (ABUNDANCE, 'CHEBI', 'mevalonate'), {
         RELATION: HAS_PRODUCT,
     }),
    ((
         REACTION,
         (
             (ABUNDANCE, 'CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
             (ABUNDANCE, 'CHEBI', 'NADPH'),
             (ABUNDANCE, 'CHEBI', 'hydron')
         ),
         (
             (ABUNDANCE, 'CHEBI', 'NADP(+)'),
             (ABUNDANCE, 'CHEBI', 'mevalonate')
         )
     ),
     (ABUNDANCE, 'CHEBI', 'NADP(+)'), {
         RELATION: HAS_PRODUCT,
     }),
    ((
         REACTION,
         (
             (ABUNDANCE, 'CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
             (ABUNDANCE, 'CHEBI', 'NADPH'),
             (ABUNDANCE, 'CHEBI', 'hydron')
         ),
         (
             (ABUNDANCE, 'CHEBI', 'NADP(+)'),
             (ABUNDANCE, 'CHEBI', 'mevalonate')
         )
     ),
     (BIOPROCESS, 'GOBP', 'cholesterol biosynthetic process'),
     {
         EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
         CITATION: citation_2,
         RELATION: SUBPROCESS_OF,
     }),
    ((ABUNDANCE, 'CHEBI', 'nitric oxide'),
     (COMPLEX, (PROTEIN, 'HGNC', 'ITGAV'), (PROTEIN, 'HGNC', 'ITGB3')), {
         EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
         CITATION: citation_2,
         RELATION: INCREASES,
         OBJECT: {
             MODIFIER: TRANSLOCATION,
             EFFECT: {
                 FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'intracellular'},
                 TO_LOC: {NAMESPACE: 'GOCC', NAME: 'cell surface'}
             }
         },
     }),
    ((COMPLEX, (PROTEIN, 'HGNC', 'ITGAV'), (PROTEIN, 'HGNC', 'ITGB3')), (PROTEIN, 'HGNC', 'ITGAV'), {
        RELATION: HAS_COMPONENT,
    }),
    ((COMPLEX, (PROTEIN, 'HGNC', 'ITGAV'), (PROTEIN, 'HGNC', 'ITGB3')), (PROTEIN, 'HGNC', 'ITGB3'), {
        RELATION: HAS_COMPONENT,
    }),
    ((GENE, 'HGNC', 'ARRDC2'), (GENE, 'HGNC', 'ARRDC3'), {
        RELATION: EQUIVALENT_TO,
        CITATION: citation_2,
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification'
    }),
    ((GENE, 'HGNC', 'ARRDC3'), (GENE, 'HGNC', 'ARRDC2'), {
        RELATION: EQUIVALENT_TO,
        CITATION: citation_2,
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification'
    }),
    ((GENE, 'dbSNP', 'rs123456'), (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')), {
        RELATION: ASSOCIATION,
        CITATION: citation_2,
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification'
    }),
    ((GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')), (GENE, 'dbSNP', 'rs123456'), {
        RELATION: ASSOCIATION,
        CITATION: citation_2,
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification'
    }),
]
