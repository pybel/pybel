# -*- coding: utf-8 -*-

"""Constants for PyBEL tests."""

import logging
import os
import unittest
from json import dumps

from requests.compat import urlparse

from pybel import BELGraph
from pybel.constants import (
    ABUNDANCE, ACTIVITY, ANNOTATIONS, ASSOCIATION, BEL_DEFAULT_NAMESPACE, BIOPROCESS, CAUSES_NO_CHANGE, CITATION,
    CITATION_NAME, CITATION_REFERENCE, CITATION_TYPE, COMPLEX, COMPOSITE, DECREASES, DEGRADATION, DIRECTLY_DECREASES,
    DIRECTLY_INCREASES, EFFECT, EQUIVALENT_TO, EVIDENCE, FRAGMENT, FRAUNHOFER_RESOURCES, FROM_LOC, GENE, GMOD,
    HAS_COMPONENT, HAS_PRODUCT, HAS_REACTANT, HAS_VARIANT, HGVS, INCREASES, IS_A, LOCATION, METADATA_AUTHORS,
    METADATA_CONTACT, METADATA_COPYRIGHT, METADATA_DESCRIPTION, METADATA_LICENSES, METADATA_NAME, METADATA_PROJECT,
    METADATA_VERSION, MIRNA, MODIFIER, NAME, NAMESPACE, OBJECT, OPENBEL_ANNOTATION_RESOURCES,
    OPENBEL_NAMESPACE_RESOURCES, PATHOLOGY, PMOD, POSITIVE_CORRELATION, PROTEIN, RATE_LIMITING_STEP_OF, REACTION,
    REGULATES, RELATION, RNA, SUBJECT, SUBPROCESS_OF, TO_LOC, TRANSCRIBED_TO, TRANSLATED_TO, TRANSLOCATION,
)
from pybel.dsl import complex_abundance, pathology, protein, translocation
from pybel.parser.exc import (
    BelSyntaxError, IllegalAnnotationValueWarning, InvalidCitationLengthException, InvalidCitationType,
    InvalidFunctionSemantic, InvalidPubMedIdentifierWarning, MalformedTranslocationWarning, MissingAnnotationKeyWarning,
    MissingAnnotationRegexWarning, MissingCitationException, MissingMetadataException, MissingNamespaceNameWarning,
    MissingNamespaceRegexWarning, MissingSupportWarning, NakedNameWarning, NestedRelationWarning,
    PlaceholderAminoAcidWarning, UndefinedAnnotationWarning, UndefinedNamespaceWarning, VersionFormatWarning,
)
from pybel.parser.parse_bel import BelParser
from pybel.utils import subdict_matches

log = logging.getLogger(__name__)

test_citation_dict = {
    CITATION_TYPE: 'PubMed',
    CITATION_NAME: 'TestName',
    CITATION_REFERENCE: '1235813'
}
SET_CITATION_TEST = 'SET Citation = {{"{type}","{name}","{reference}"}}'.format(**test_citation_dict)
test_evidence_text = 'I read it on Twitter'
test_set_evidence = 'SET Evidence = "{}"'.format(test_evidence_text)

CHEBI_KEYWORD = 'CHEBI'
CHEBI_URL = OPENBEL_NAMESPACE_RESOURCES + 'chebi.belns'
CELL_LINE_KEYWORD = 'CellLine'
CELL_LINE_URL = OPENBEL_ANNOTATION_RESOURCES + 'cell-line.belanno'
HGNC_KEYWORD = 'HGNC'
HGNC_URL = OPENBEL_NAMESPACE_RESOURCES + 'hgnc-human-genes.belns'
MESH_DISEASES_KEYWORD = 'MeSHDisease'
MESH_DISEASES_URL = OPENBEL_ANNOTATION_RESOURCES + "mesh-diseases.belanno"

test_connection = os.environ.get('PYBEL_TEST_CONNECTION')


def update_provenance(control_parser):
    """Put a default evidence and citation in a BEL parser.
    
    :param pybel.parser.parse_control.ControlParser control_parser:
    """
    control_parser.citation.update(test_citation_dict)
    control_parser.evidence = test_evidence_text


def assert_has_node(self, node, graph, **kwargs):
    """Check if a node with the given properties is contained within a graph.

    :param self: A Test Case
    :type self: unittest.TestCase
    :param node: 
    :param graph:
    :type graph: BELGraph
    :param kwargs:
    """
    self.assertTrue(graph.has_node(node), msg='{} not found in graph'.format(node))
    if kwargs:
        missing = set(kwargs) - set(graph.node[node])
        self.assertFalse(missing, msg="Missing {} in node data".format(', '.join(sorted(missing))))
        self.assertTrue(all(kwarg in graph.node[node] for kwarg in kwargs),
                        msg="Missing kwarg in node data")
        self.assertEqual(kwargs, {k: graph.node[node][k] for k in kwargs},
                         msg="Wrong values in node data")


def any_dict_matches(dict_of_dicts, query_dict):
    """

    :param dict_of_dicts:
    :param query_dict:
    :return:
    """
    return any(
        query_dict == sd
        for sd in dict_of_dicts.values()
    )


def any_subdict_matches(dict_of_dicts, query_dict):
    """Checks if dictionary target_dict matches one of the subdictionaries of a

    :param dict[any,dict] dict_of_dicts: dictionary of dictionaries
    :param dict query_dict: dictionary
    :return: if dictionary target_dict matches one of the subdictionaries of a
    :rtype: bool
    """
    return any(
        subdict_matches(sub_dict, query_dict)
        for sub_dict in dict_of_dicts.values()
    )


def assert_has_edge(self, u, v, graph, permissive=True, **kwargs):
    """A helper function for checking if an edge with the given properties is contained within a graph

    :param unittest.TestCase self: A TestCase
    :param tuple u: source node
    :param tuple v: target node
    :param BELGraph graph: underlying graph
    """
    self.assertTrue(graph.has_edge(u, v), msg='Edge ({}, {}) not in graph'.format(u, v))

    if not kwargs:
        return

    if permissive:
        matches = any_subdict_matches(graph.edge[u][v], kwargs)
    else:
        matches = any_dict_matches(graph.edge[u][v], kwargs)

    msg = 'No edge ({}, {}) with correct properties. expected:\n {}\nbut got:\n{}'.format(
        u,
        v,
        dumps(kwargs, indent=2, sort_keys=True),
        dumps(graph.edge[u][v], indent=2, sort_keys=True)
    )
    self.assertTrue(matches, msg=msg)


class TestGraphMixin(unittest.TestCase):
    """A test case with additional functions for testing graphs."""

    def assert_has_node(self, g, n, **kwargs):
        """Help assert node membership.
        
        :param g: Graph 
        :param n: Node
        :param kwargs: 
        """
        assert_has_node(self, n, g, **kwargs)

    def assert_has_edge(self, g, u, v, **kwargs):
        """Help assert edge membership.
        
        :param g: Graph
        :param u: Source node
        :param v: Target node
        :param kwargs: 
        """
        assert_has_edge(self, u, v, g, **kwargs)


class TestTokenParserBase(unittest.TestCase):
    """A test case that has a BEL parser available."""

    @classmethod
    def setUpClass(cls):
        """Build a BEL graph and BEL parser that persist through the class."""
        cls.graph = BELGraph()
        cls.parser = BelParser(cls.graph, autostreamline=False)

    def setUp(self):
        """Clear the parser at the beginning of each test."""
        self.parser.clear()

    def assert_has_node(self, member, **kwargs):
        """Assert that this test case's graph has the given node."""
        assert_has_node(self, member, self.graph, **kwargs)

    def assert_has_edge(self, u, v, **kwargs):
        """Assert that this test case's graph has the given edge."""
        assert_has_edge(self, u, v, self.graph, **kwargs)

    def add_default_provenance(self):
        """Add a default citation and evidence to the parser."""
        update_provenance(self.parser.control_parser)


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

expected_test_slushy_metadata = {
    METADATA_NAME: "Worst. BEL Document. Ever.",
    METADATA_DESCRIPTION: "This document outlines all of the evil and awful work that is possible during BEL curation",
    METADATA_VERSION: "0.0",
    METADATA_AUTHORS: "Charles Tapley Hoyt",
    METADATA_LICENSES: "WTF License",
}


def get_uri_name(url):
    """Get the file name from the end of the URL.

    Only useful for PyBEL's testing though since it looks specifically if the file is from the weird owncloud
    resources distributed by Fraunhofer.
    """
    url_parsed = urlparse(url)

    if url.startswith(FRAUNHOFER_RESOURCES):
        return url_parsed.query.split('=')[-1]
    else:
        url_parts = url_parsed.path.split('/')
        return url_parts[-1]


def help_check_hgnc(test_case, namespace_dict):
    """Assert that the namespace dictionary is correct.

    :param unittest.TestCase test_case:
    :param namespace_dict:
    :return:
    """
    test_case.assertIn(HGNC_KEYWORD, namespace_dict)

    test_case.assertIn('MHS2', namespace_dict[HGNC_KEYWORD])
    test_case.assertEqual(set('G'), set(namespace_dict[HGNC_KEYWORD]['MHS2']))

    test_case.assertIn('MIATNB', namespace_dict[HGNC_KEYWORD])
    test_case.assertEqual(set('GR'), set(namespace_dict[HGNC_KEYWORD]['MIATNB']))

    test_case.assertIn('MIA', namespace_dict[HGNC_KEYWORD])
    test_case.assertEqual(set('GRP'), set(namespace_dict[HGNC_KEYWORD]['MIA']))


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


class BelReconstitutionMixin(TestGraphMixin):
    """A test case that has checks for properly loading several BEL Scripts."""

    def bel_simple_reconstituted(self, graph, check_metadata=True):
        """Check that test_bel.bel was loaded properly.

        :param BELGraph graph: A BEL grpah
        :param bool check_metadata: Check the graph's document section is correct
        """
        self.assertIsNotNone(graph)
        self.assertIsInstance(graph, BELGraph)

        if check_metadata:
            self.assertIsNotNone(graph.document)
            self.assertEqual(expected_test_simple_metadata[METADATA_NAME], graph.name)
            self.assertEqual(expected_test_simple_metadata[METADATA_VERSION], graph.version)

        self.assertEqual(4, graph.number_of_nodes())

        # FIXME this should work, but is getting 8 for the upgrade function
        # self.assertEqual(6, graph.number_of_edges(),
        #                  msg='Edges:\n{}'.format('\n'.join(map(str, graph.edges(keys=True, data=True)))))

        self.assertTrue(graph.has_node_with_data(protein(namespace='HGNC', name='AKT1')))
        self.assertTrue(graph.has_node_with_data(protein(namespace='HGNC', name='EGFR')))
        self.assertTrue(graph.has_node_with_data(protein(namespace='HGNC', name='FADD')))
        self.assertTrue(graph.has_node_with_data(protein(namespace='HGNC', name='CASP8')))

        bel_simple_citation_1 = {
            CITATION_NAME: "That one article from last week",
            CITATION_REFERENCE: "123455",
            CITATION_TYPE: "PubMed"
        }

        bel_simple_citation_2 = {
            CITATION_NAME: "That other article from last week",
            CITATION_REFERENCE: "123456",
            CITATION_TYPE: "PubMed"
        }

        evidence_1_extra = "Evidence 1 w extra notes"
        evidence_2 = 'Evidence 2'
        evidence_3 = 'Evidence 3'

        assert_has_edge(self, AKT1, EGFR, graph, **{
            RELATION: INCREASES,
            CITATION: bel_simple_citation_1,
            EVIDENCE: evidence_1_extra,
            ANNOTATIONS: {
                'Species': {'9606': True}
            }
        })
        assert_has_edge(self, EGFR, FADD, graph, **{
            RELATION: DECREASES,
            ANNOTATIONS: {
                'Species': {'9606': True},
                'CellLine': {'10B9 cell': True}
            },
            CITATION: bel_simple_citation_1,
            EVIDENCE: evidence_2
        })
        assert_has_edge(self, EGFR, CASP8, graph, **{
            RELATION: DIRECTLY_DECREASES,
            ANNOTATIONS: {
                'Species': {'9606': True},
                'CellLine': {'10B9 cell': True}
            },
            CITATION: bel_simple_citation_1,
            EVIDENCE: evidence_2,
        })
        assert_has_edge(self, FADD, CASP8, graph, **{
            RELATION: INCREASES,
            ANNOTATIONS: {
                'Species': {'10116': True}
            },
            CITATION: bel_simple_citation_2,
            EVIDENCE: evidence_3,
        })
        assert_has_edge(self, AKT1, CASP8, graph, **{
            RELATION: ASSOCIATION,
            ANNOTATIONS: {
                'Species': {'10116': True}
            },
            CITATION: bel_simple_citation_2,
            EVIDENCE: evidence_3,
        })
        assert_has_edge(self, CASP8, AKT1, graph, **{
            RELATION: ASSOCIATION,
            ANNOTATIONS: {
                'Species': {'10116': True}
            },
            CITATION: bel_simple_citation_2,
            EVIDENCE: evidence_3,
        })

    def bel_thorough_reconstituted(self, graph, check_metadata=True, check_warnings=True, check_provenance=True,
                                   check_citation_name=True):
        """Check that thorough.bel was loaded properly.

        :param BELGraph graph: A BEL graph
        :param bool check_metadata: Check the graph's document section is correct
        :param bool check_warnings: Check the graph produced the expected warnings
        :param bool check_provenance: Check the graph's definition section is correct
        :param bool check_citation_name: Check that the names in the citations get reconstituted. This isn't strictly
                                         necessary since this data can be looked up
        """
        self.assertIsNotNone(graph)
        self.assertIsInstance(graph, BELGraph)

        if check_warnings:
            self.assertEqual(0, len(graph.warnings),
                             msg='Document warnings:\n{}'.format('\n'.join(map(str, graph.warnings))))

        if check_metadata:
            self.assertLessEqual(set(expected_test_thorough_metadata), set(graph.document))
            self.assertEqual(expected_test_thorough_metadata[METADATA_NAME], graph.name)
            self.assertEqual(expected_test_thorough_metadata[METADATA_VERSION], graph.version)
            self.assertEqual(expected_test_thorough_metadata[METADATA_DESCRIPTION], graph.description)

        if check_provenance:
            self.assertEqual({'CHEBI', 'HGNC', 'GOBP', 'GOCC', 'MESHD', 'TESTNS2'}, set(graph.namespace_url))
            self.assertEqual({'dbSNP'}, set(graph.namespace_pattern))
            self.assertEqual({'TESTAN1', 'TESTAN2'}, set(graph.annotation_list))
            self.assertEqual({'TestRegex'}, set(graph.annotation_pattern))

        self.assertEqual(set(BEL_THOROUGH_NODES), set(graph))

        # FIXME
        # self.assertEqual(set((u, v) for u, v, _ in e), set(g.edges()))

        self.assertLess(0, graph.number_of_edges())

        for u, v, d in BEL_THOROUGH_EDGES:

            if not check_citation_name and CITATION in d and CITATION_NAME in d[CITATION]:
                d[CITATION] = d[CITATION].copy()
                del d[CITATION][CITATION_NAME]

            assert_has_edge(self, u, v, graph, permissive=True, **d)

    def bel_slushy_reconstituted(self, graph, check_metadata=True, check_warnings=True):
        """Check that slushy.bel was loaded properly.
        
        :param BELGraph graph: A BEL graph
        :param bool check_metadata: Check the graph's document section is correct
        :param bool check_warnings: Check the graph produced the expected warnings
        """
        self.assertIsNotNone(graph)
        self.assertIsInstance(graph, BELGraph)

        if check_metadata:
            self.assertIsNotNone(graph.document)
            self.assertIsInstance(graph.document, dict)
            self.assertEqual(expected_test_slushy_metadata[METADATA_NAME], graph.name)
            self.assertEqual(expected_test_slushy_metadata[METADATA_VERSION], graph.version)
            self.assertEqual(expected_test_slushy_metadata[METADATA_DESCRIPTION], graph.description)

        if check_warnings:
            expected_warnings = [
                (0, MissingMetadataException),
                (3, VersionFormatWarning),
                (26, MissingAnnotationKeyWarning),
                (29, MissingAnnotationKeyWarning),
                (34, InvalidCitationLengthException),
                (37, InvalidCitationType),
                (40, InvalidPubMedIdentifierWarning),
                (43, MissingCitationException),
                (48, MissingAnnotationKeyWarning),
                (51, MissingAnnotationKeyWarning),
                (54, MissingSupportWarning),
                (59, NakedNameWarning),
                (62, UndefinedNamespaceWarning),
                (65, MissingNamespaceNameWarning),
                (68, UndefinedAnnotationWarning),
                (71, MissingAnnotationKeyWarning),
                (74, IllegalAnnotationValueWarning),
                (77, MissingAnnotationRegexWarning),
                (80, MissingNamespaceRegexWarning),
                (83, MalformedTranslocationWarning),
                (86, PlaceholderAminoAcidWarning),
                (89, NestedRelationWarning),
                (92, InvalidFunctionSemantic),
                # (95, Exception),
                (98, BelSyntaxError),
            ]

            for (el, ew), (l, _, w, _) in zip(expected_warnings, graph.warnings):
                self.assertEqual(el, l, msg="Expected different error on line {}. Check line {}".format(el, l))
                self.assertIsInstance(w, ew, msg='Line: {}'.format(el))

        self.assertTrue(graph.has_node_with_data(protein(namespace='HGNC', name='AKT1')))
        self.assertTrue(graph.has_node_with_data(protein(namespace='HGNC', name='EGFR')))

        self.assertLess(0, graph.number_of_edges())

        assert_has_edge(self, AKT1, EGFR, graph, **{
            RELATION: INCREASES,
            CITATION: citation_1,
            EVIDENCE: evidence_1,
        })

    def bel_isolated_reconstituted(self, graph):
        """Run the isolated node test.

        :type graph: BELGraph
        """
        self.assertIsNotNone(graph)
        self.assertIsInstance(graph, BELGraph)

        adgrb1 = protein(namespace='HGNC', name='ADGRB1')
        adgrb2 = protein(namespace='HGNC', name='ADGRB2')
        adgrb_complex = complex_abundance([adgrb1, adgrb2])
        achlorhydria = pathology(namespace='MESHD', name='Achlorhydria')

        self.assertTrue(graph.has_node_with_data(adgrb1))
        self.assertTrue(graph.has_node_with_data(adgrb2))
        self.assertTrue(graph.has_node_with_data(adgrb_complex))
        self.assertTrue(graph.has_node_with_data(achlorhydria))

        b = adgrb1.as_tuple()
        c = adgrb2.as_tuple()
        d = adgrb_complex.as_tuple()

        assert_has_edge(self, d, b, graph)
        assert_has_edge(self, d, c, graph)
