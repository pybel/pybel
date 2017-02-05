# -*- coding: utf-8 -*-

import json
import logging
import os
import unittest

import networkx as nx
from onto2nx.ontospy import Ontospy
from requests.compat import urlparse

from pybel import BELGraph
from pybel.constants import CITATION_TYPE, CITATION_NAME, CITATION_REFERENCE
from pybel.constants import DEGRADATION, FROM_LOC, TO_LOC, HAS_COMPONENT
from pybel.constants import FUNCTION, NAMESPACE, NAME
from pybel.constants import INCREASES, DECREASES, ASSOCIATION, MODIFIER, EFFECT, ACTIVITY
from pybel.constants import KIND, TRANSLOCATION
from pybel.constants import LOCATION, CITATION, EVIDENCE
from pybel.constants import PROTEIN, ABUNDANCE, GENE, RNA, MIRNA, COMPLEX, \
    COMPOSITE, BIOPROCESS, PATHOLOGY, REACTION, PMOD, HGVS, GMOD, PYBEL_DEFAULT_NAMESPACE, FRAGMENT
from pybel.constants import RELATION, EQUIVALENT_TO, HAS_VARIANT, HAS_REACTANT, HAS_PRODUCT, SUBJECT, OBJECT
from pybel.manager.utils import urldefrag, OWLParser
from pybel.parser.modifiers import VariantParser
from pybel.parser.parse_bel import BelParser
from pybel.parser.utils import any_subdict_matches

try:
    from unittest import mock
except ImportError:
    import mock

dir_path = os.path.dirname(os.path.realpath(__file__))
owl_dir_path = os.path.join(dir_path, 'owl')
bel_dir_path = os.path.join(dir_path, 'bel')
belns_dir_path = os.path.join(dir_path, 'belns')
belanno_dir_path = os.path.join(dir_path, 'belanno')
beleq_dir_path = os.path.join(dir_path, 'beleq')

test_bel = os.path.join(bel_dir_path, 'test_bel.bel')
test_bel_4 = os.path.join(bel_dir_path, 'test_bel_owl_extension.bel')
test_bel_slushy = os.path.join(bel_dir_path, 'slushy.bel')
test_bel_thorough = os.path.join(bel_dir_path, 'thorough.bel')

test_owl_1 = os.path.join(owl_dir_path, 'pizza_onto.owl')
test_owl_2 = os.path.join(owl_dir_path, 'wine.owl')
test_owl_3 = os.path.join(owl_dir_path, 'ado.owl')

test_an_1 = os.path.join(belanno_dir_path, 'test_an_1.belanno')

test_ns_1 = os.path.join(belns_dir_path, 'test_ns_1.belns')
test_ns_2 = os.path.join(belns_dir_path, 'test_ns_1_updated.belns')

test_eq_1 = os.path.join(beleq_dir_path, 'disease-ontology.beleq')
test_eq_2 = os.path.join(beleq_dir_path, 'mesh-diseases.beleq')

test_citation_dict = {
    CITATION_TYPE: 'PubMed',
    CITATION_NAME: 'TestName',
    CITATION_REFERENCE: '1235813'
}
test_citation_bel = 'SET Citation = {{"{type}","{name}","{reference}"}}'.format(**test_citation_dict)
test_evidence_text = 'I read it on Twitter'
test_evidence_bel = 'SET Evidence = "{}"'.format(test_evidence_text)

CHEBI_KEYWORD = 'CHEBI'
CHEBI_URL = 'http://resources.openbel.org/belframework/20150611/namespace/chebi.belns'
CELL_LINE_KEYWORD = 'CellLine'
CELL_LINE_URL = 'http://resources.openbel.org/belframework/20150611/annotation/cell-line.belanno'
HGNC_KEYWORD = 'HGNC'
HGNC_URL = 'http://resources.openbel.org/belframework/20150611/namespace/hgnc-human-genes.belns'
MESH_DISEASES_KEYWORD = 'MeSHDisease'
MESH_DISEASES_URL = "http://resources.openbel.org/belframework/20150611/annotation/mesh-diseases.belanno"

pizza_iri = 'http://www.lesfleursdunormal.fr/static/_downloads/pizza_onto.owl'
wine_iri = 'http://www.w3.org/TR/2003/PR-owl-guide-20031209/wine'

AKT1 = (PROTEIN, 'HGNC', 'AKT1')
EGFR = (PROTEIN, 'HGNC', 'EGFR')
FADD = (PROTEIN, 'HGNC', 'FADD')
CASP8 = (PROTEIN, 'HGNC', 'CASP8')

log = logging.getLogger(PYBEL_DEFAULT_NAMESPACE)


def assertHasNode(self, member, graph, **kwargs):
    self.assertTrue(graph.has_node(member), msg='{} not found in {}'.format(member, graph))
    if kwargs:
        missing = set(kwargs) - set(graph.node[member])
        self.assertFalse(missing, msg="Missing {} in node data".format(', '.join(sorted(missing))))
        self.assertTrue(all(kwarg in graph.node[member] for kwarg in kwargs),
                        msg="Missing kwarg in node data")
        self.assertEqual(kwargs, {k: graph.node[member][k] for k in kwargs},
                         msg="Wrong values in node data")


def assertHasEdge(self, u, v, graph, **kwargs):
    """
    :param self: unittest.TestCase
    :param u: source node
    :param v: target node
    :param graph: underlying graph
    :param kwargs: splat the data to match
    :return:
    """
    self.assertTrue(graph.has_edge(u, v), msg='Edge ({}, {}) not in graph {}'.format(u, v, graph))
    if kwargs:
        msg_format = 'No edge ({}, {}) with correct properties. expected:\n {}\nbut got:\n{}'
        self.assertTrue(any_subdict_matches(graph.edge[u][v], kwargs),
                        msg=msg_format.format(u, v, json.dumps(kwargs, indent=2, sort_keys=True),
                                              json.dumps(graph.edge[u][v], indent=2, sort_keys=True)))


class TestTokenParserBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = BelParser(complete_origin=True)

    def setUp(self):
        self.parser.clear()

    def assertHasNode(self, member, **kwargs):
        assertHasNode(self, member, self.parser.graph, **kwargs)

    def assertHasEdge(self, u, v, **kwargs):
        assertHasEdge(self, u, v, self.parser.graph, **kwargs)


expected_test_bel_metadata = {
    'name': "PyBEL Test Document 1",
    "description": "Made for testing PyBEL parsing",
    'version': "1.6",
    'copyright': "Copyright (c) Charles Tapley Hoyt. All Rights Reserved.",
    'authors': "Charles Tapley Hoyt",
    'licenses': "WTF License",
    'contact': "charles.hoyt@scai.fraunhofer.de"
}

expected_test_bel_3_metadata = {
    'name': "PyBEL Test Document 3",
    "description": "Made for testing PyBEL parsing",
    'version': "1.6",
    'copyright': "Copyright (c) Charles Tapley Hoyt. All Rights Reserved.",
    'authors': "Charles Tapley Hoyt",
    'licenses': "WTF License",
    'contact': "charles.hoyt@scai.fraunhofer.de"
}

expected_test_bel_4_metadata = {
    'name': "PyBEL Test Document 4",
    'description': "Tests the use of OWL ontologies as namespaces",
    'version': "1.6",
    'copyright': "Copyright (c) Charles Tapley Hoyt. All Rights Reserved.",
    'authors': "Charles Tapley Hoyt",
    'licenses': "WTF License",
    'contact': "charles.hoyt@scai.fraunhofer.de"
}


def build_variant_dict(variant):
    return {KIND: HGVS, VariantParser.IDENTIFIER: variant}


def get_uri_name(url):
    url_parsed = urlparse(url)
    url_parts = url_parsed.path.split('/')
    return url_parts[-1]


class MockResponse:
    """See http://stackoverflow.com/questions/15753390/python-mock-requests-and-the-response"""

    def __init__(self, mock_url):
        name = get_uri_name(mock_url)

        if mock_url.endswith('.belns'):
            self.path = os.path.join(belns_dir_path, name)
        elif mock_url.endswith('.belanno'):
            self.path = os.path.join(belanno_dir_path, name)
        elif mock_url.endswith('.beleq'):
            self.path = os.path.join(beleq_dir_path, name)
        elif mock_url == wine_iri:
            self.path = test_owl_2
        elif mock_url == pizza_iri:
            self.path = test_owl_1
        else:
            raise ValueError('Invalid extension')

        if not os.path.exists(self.path):
            raise ValueError("file doesn't exist: {}".format(self.path))

    def iter_lines(self):
        with open(self.path, 'rb') as f:
            for line in f:
                yield line


class MockSession:
    """Patches the session object so requests can be redirected through the filesystem without rewriting BEL files"""

    def __init__(self):
        pass

    def mount(self, prefix, adapter):
        pass

    @staticmethod
    def get(url):
        return MockResponse(url)


mock_bel_resources = mock.patch('pybel.utils.requests.Session', side_effect=MockSession)


def help_check_hgnc(self, namespace_dict):
    self.assertIn(HGNC_KEYWORD, namespace_dict)

    self.assertIn('MHS2', namespace_dict[HGNC_KEYWORD])
    self.assertEqual(set('G'), set(namespace_dict[HGNC_KEYWORD]['MHS2']))

    self.assertIn('MIATNB', namespace_dict[HGNC_KEYWORD])
    self.assertEqual(set('GR'), set(namespace_dict[HGNC_KEYWORD]['MIATNB']))

    self.assertIn('MIA', namespace_dict[HGNC_KEYWORD])
    self.assertEqual(set('GRP'), set(namespace_dict[HGNC_KEYWORD]['MIA']))


def parse_owl_pybel_resolver(iri):
    path = os.path.join(owl_dir_path, get_uri_name(iri))

    if not os.path.exists(path) and '.' not in path:
        path = '{}.owl'.format(path)

    return OWLParser(file=path)


mock_parse_owl_pybel = mock.patch('pybel.manager.utils.parse_owl_pybel', side_effect=parse_owl_pybel_resolver)


def parse_owl_rdf_resolver(iri):
    path = os.path.join(owl_dir_path, get_uri_name(iri))
    o = Ontospy(path)

    g = nx.DiGraph(IRI=iri)

    for cls in o.classes:
        g.add_node(cls.locale, type='Class')

        for parent in cls.parents():
            g.add_edge(cls.locale, parent.locale, type='SubClassOf')

        for instance in cls.instances():
            _, frag = urldefrag(instance)
            g.add_edge(frag, cls.locale, type='ClassAssertion')

    return g


mock_parse_owl_rdf = mock.patch('pybel.manager.utils.parse_owl_rdf', side_effect=parse_owl_rdf_resolver)


class BelReconstitutionMixin(unittest.TestCase):
    def bel_1_reconstituted(self, g, check_metadata=True):
        self.assertIsNotNone(g)
        self.assertIsInstance(g, BELGraph)

        # FIXME this doesn't work for GraphML IO
        if check_metadata:
            self.assertEqual(expected_test_bel_metadata, g.document)

        assertHasNode(self, AKT1, g, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'AKT1'})
        assertHasNode(self, EGFR, g, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'EGFR'})
        assertHasNode(self, FADD, g, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'FADD'})
        assertHasNode(self, CASP8, g, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'CASP8'})

        assertHasEdge(self, AKT1, EGFR, g, relation=INCREASES, TESTAN1="1")
        assertHasEdge(self, EGFR, FADD, g, relation=DECREASES, TESTAN1="1", TESTAN2="3")
        assertHasEdge(self, EGFR, CASP8, g, relation='directlyDecreases', TESTAN1="1", TESTAN2="3")
        assertHasEdge(self, FADD, CASP8, g, relation=INCREASES, TESTAN1="2")
        assertHasEdge(self, AKT1, CASP8, g, relation='association', TESTAN1="2")

    def bel_thorough_reconstituted(self, g, check_metadata=True):
        self.assertIsNotNone(g)
        self.assertIsInstance(g, BELGraph)
        self.assertEqual(0, len(g.warnings), msg='Document warnings:\n{}'.format('\n'.join(map(str, g.warnings))))

        self.assertEqual({'CHEBI', 'HGNC', 'GOBP', 'GOCC', 'MESHD', 'TESTNS2'}, set(g.namespace_url))
        self.assertEqual(set(), set(g.namespace_owl))
        self.assertEqual({'dbSNP'}, set(g.namespace_pattern))
        self.assertEqual(set(), set(g.annotation_owl))
        self.assertEqual({'TESTAN1', 'TESTAN2'}, set(g.annotation_list))

        x = {
            (ABUNDANCE, 'CHEBI', 'oxygen atom'),
            (GENE, 'HGNC', 'AKT1', (GMOD, (PYBEL_DEFAULT_NAMESPACE, 'Me'))),
            (GENE, 'HGNC', 'AKT1'),
            (GENE, 'HGNC', 'AKT1', (HGVS, 'p.Phe508del')),
            (PROTEIN, 'HGNC', 'AKT1'),
            (GENE, 'HGNC', 'AKT1', (HGVS, 'c.308G>A')),
            (GENE, ('HGNC', 'TMPRSS2'), ('c', 1, 79), ('HGNC', 'ERG'), ('c', 312, 5034)),
            (GENE, 'HGNC', 'AKT1', (HGVS, 'c.1521_1523delCTT'), (HGVS, 'c.308G>A'), (HGVS, 'p.Phe508del')),
            (MIRNA, 'HGNC', 'MIR21'),
            (GENE, ('HGNC', 'BCR'), ('c', '?', 1875), ('HGNC', 'JAK2'), ('c', 2626, '?')),
            (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')),
            (GENE, 'HGNC', 'CFTR'),
            (GENE, 'HGNC', 'CFTR', (HGVS, 'g.117199646_117199648delCTT')),
            (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')),
            (PROTEIN, 'HGNC', 'AKT1', (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 473)),
            (MIRNA, 'HGNC', 'MIR21', (HGVS, 'p.Phe508del')),
            (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.C40*')),
            (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Ala127Tyr'), (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser')),
            (GENE, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
            (PROTEIN, ('HGNC', 'TMPRSS2'), ('p', 1, 79), ('HGNC', 'ERG'), ('p', 312, 5034)),
            (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Arg1851*')),
            (PROTEIN, ('HGNC', 'BCR'), ('p', '?', 1875), ('HGNC', 'JAK2'), ('p', 2626, '?')),
            (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.40*')),
            (PROTEIN, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
            (PROTEIN, 'HGNC', 'CFTR', (HGVS, '=')),
            (PROTEIN, 'HGNC', 'CFTR'),
            (PROTEIN, 'HGNC', 'EGFR'),
            (PROTEIN, 'HGNC', 'CFTR', (HGVS, '?')),
            (PATHOLOGY, 'MESHD', 'Adenocarcinoma'),
            (PROTEIN, 'HGNC', 'CFTR', (HGVS, 'p.Phe508del')),
            (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, (5, 20))),
            (PROTEIN, 'HGNC', 'MIA'),
            (COMPLEX, 'GOCC', 'interleukin-23 complex'),
            (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, (1, '?'))),
            (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, '?')),
            (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, '?', '55kD')),
            (PROTEIN, 'HGNC', 'CFTR', (HGVS, 'p.Gly576Ala')),
            (RNA, 'HGNC', 'AKT1'),
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
            (REACTION, ((ABUNDANCE, ('CHEBI', 'superoxide')),),
             ((ABUNDANCE, ('CHEBI', 'dioxygen')), (ABUNDANCE, ('CHEBI', 'hydrogen peroxide')))),
            (ABUNDANCE, 'CHEBI', 'superoxide'),
            (ABUNDANCE, 'CHEBI', 'hydrogen peroxide'),
            (ABUNDANCE, 'CHEBI', 'dioxygen'),
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
            (PROTEIN, 'HGNC', 'GSK3B', (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 9)),
            (PROTEIN, 'HGNC', 'GSK3B'),
            (PATHOLOGY, 'MESHD', 'Psoriasis'),
            (PATHOLOGY, 'MESHD', 'Skin Diseases'),
            (REACTION,
             ((ABUNDANCE, ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), (ABUNDANCE, ('CHEBI', 'NADPH')),
              (ABUNDANCE, ('CHEBI', 'hydron'))),
             ((ABUNDANCE, ('CHEBI', 'NADP(+)')), (ABUNDANCE, ('CHEBI', 'mevalonate')))),
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
            (PROTEIN, 'HGNC', 'HRAS', (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Palm'))),
            (BIOPROCESS, 'GOBP', 'apoptotic process'),
            (COMPOSITE, (ABUNDANCE, 'TESTNS2', 'Abeta_42'), (PROTEIN, 'HGNC', 'CASP8'),
             (PROTEIN, 'HGNC', 'FADD')),
            (REACTION, ((PROTEIN, ('HGNC', 'CDK5R1')),), ((PROTEIN, ('HGNC', 'CDK5')),)),
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
            (PROTEIN, 'HGNC', 'MAPT', (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'))),
            (PROTEIN, 'HGNC', 'MAPT'),
            (GENE, 'HGNC', 'ARRDC2'),
            (GENE, 'HGNC', 'ARRDC3'),
            (GENE, 'dbSNP', 'rs123456')
        }

        self.assertEqual(x, set(g.nodes()))

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

        e = [
            ((ABUNDANCE, 'CHEBI', 'oxygen atom'), (GENE, 'HGNC', 'AKT1', (GMOD, (PYBEL_DEFAULT_NAMESPACE, 'Me'))),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: INCREASES}),
            ((GENE, 'HGNC', 'AKT1'), (GENE, 'HGNC', 'AKT1', (GMOD, (PYBEL_DEFAULT_NAMESPACE, 'Me'))),
             {RELATION: HAS_VARIANT}),
            ((GENE, 'HGNC', 'AKT1'), (ABUNDANCE, 'CHEBI', 'oxygen atom'),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: DECREASES, SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
              OBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}}}),
            ((GENE, 'HGNC', 'AKT1'), (GENE, 'HGNC', 'AKT1', (HGVS, 'p.Phe508del')), {RELATION: HAS_VARIANT}),
            ((GENE, 'HGNC', 'AKT1'), (GENE, 'HGNC', 'AKT1', (HGVS, 'c.308G>A')), {RELATION: HAS_VARIANT}),
            ((GENE, 'HGNC', 'AKT1'),
             (GENE, 'HGNC', 'AKT1', (HGVS, 'c.1521_1523delCTT'), (HGVS, 'c.308G>A'), (HGVS, 'p.Phe508del')),
             {RELATION: HAS_VARIANT}),
            ((GENE, 'HGNC', 'AKT1'), (RNA, 'HGNC', 'AKT1'),
             {EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
              CITATION: citation_2,
              RELATION: 'transcribedTo'}),
            ((GENE, 'HGNC', 'AKT1', (HGVS, 'p.Phe508del')), (PROTEIN, 'HGNC', 'AKT1'),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: 'directlyDecreases'}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1', (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 473)),
             {RELATION: HAS_VARIANT}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.C40*')), {RELATION: HAS_VARIANT}),
            ((PROTEIN, 'HGNC', 'AKT1'),
             (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Ala127Tyr'), (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser')),
             {RELATION: HAS_VARIANT}),
            ((PROTEIN, 'HGNC', 'AKT1'),
             (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Ala127Tyr'), (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser')),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: 'directlyDecreases', SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
              OBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}}}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Arg1851*')),
             {RELATION: HAS_VARIANT}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.40*')), {RELATION: HAS_VARIANT}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, '?')),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: INCREASES, SUBJECT: {MODIFIER: DEGRADATION}}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'CFTR', (HGVS, 'p.Gly576Ala')),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: INCREASES}),
            ((PROTEIN, 'HGNC', 'AKT1'), (RNA, 'HGNC', 'CFTR', (HGVS, 'r.1521_1523delcuu')),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: INCREASES,
              SUBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAMESPACE: PYBEL_DEFAULT_NAMESPACE, NAME: 'kin'}}}),
            ((PROTEIN, 'HGNC', 'AKT1'), (RNA, 'HGNC', 'CFTR', (HGVS, 'r.1653_1655delcuu')),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: INCREASES, SUBJECT: {MODIFIER: ACTIVITY, EFFECT: {}}}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'EGFR'), {
                EVIDENCE: 'These are mostly made up',
                CITATION: citation_1,
                RELATION: INCREASES,
                SUBJECT: {
                    MODIFIER: ACTIVITY,
                    EFFECT: {
                        NAMESPACE: PYBEL_DEFAULT_NAMESPACE,
                        NAME: 'cat'
                    }
                },
                OBJECT: {MODIFIER: DEGRADATION}}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'EGFR'), {
                EVIDENCE: 'These are mostly made up',
                CITATION: citation_1,
                RELATION: INCREASES,
                SUBJECT: {MODIFIER: ACTIVITY,
                          EFFECT: {NAME: 'kin',
                                   NAMESPACE: PYBEL_DEFAULT_NAMESPACE}},
                OBJECT: {MODIFIER: TRANSLOCATION,
                         EFFECT: {
                             FROM_LOC: {NAMESPACE: 'GOCC',
                                        NAME: 'intracellular'},
                             TO_LOC: {NAMESPACE: 'GOCC',
                                      NAME: 'extracellular space'}}}}),
            ((GENE, 'HGNC', 'AKT1', (HGVS, 'c.308G>A')),
             (GENE, ('HGNC', 'TMPRSS2'), ('c', 1, 79), ('HGNC', 'ERG'), ('c', 312, 5034)),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: 'causesNoChange'}),
            ((GENE, 'HGNC', 'AKT1', (HGVS, 'c.308G>A')),
             (GENE, 'HGNC', 'AKT1', (HGVS, 'c.1521_1523delCTT'), (HGVS, 'c.308G>A'), (HGVS, 'p.Phe508del')),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: INCREASES, SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}}}),
            ((MIRNA, 'HGNC', 'MIR21'),
             (GENE, ('HGNC', 'BCR'), ('c', '?', 1875), ('HGNC', 'JAK2'), ('c', 2626, '?')),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: 'directlyIncreases'}),
            ((MIRNA, 'HGNC', 'MIR21'), (PROTEIN, 'HGNC', 'AKT1', (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 473)),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: DECREASES, SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}}}),
            ((MIRNA, 'HGNC', 'MIR21'), (MIRNA, 'HGNC', 'MIR21', (HGVS, 'p.Phe508del')),
             {RELATION: HAS_VARIANT}),
            ((GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')), (PROTEIN, 'HGNC', 'AKT1'),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: INCREASES, OBJECT: {MODIFIER: DEGRADATION}}),
            ((GENE, 'HGNC', 'CFTR'), (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')), {RELATION: HAS_VARIANT}),
            ((GENE, 'HGNC', 'CFTR'), (GENE, 'HGNC', 'CFTR', (HGVS, 'g.117199646_117199648delCTT')),
             {RELATION: HAS_VARIANT}),
            ((GENE, 'HGNC', 'CFTR'), (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')),
             {RELATION: HAS_VARIANT}),
            ((GENE, 'HGNC', 'CFTR', (HGVS, 'g.117199646_117199648delCTT')),
             (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')), {
                 EVIDENCE: 'These are mostly made up',
                 CITATION: citation_1,
                 RELATION: INCREASES}),
            ((MIRNA, 'HGNC', 'MIR21', (HGVS, 'p.Phe508del')), (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.C40*')),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: INCREASES, SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}}}),
            ((GENE, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
             (PROTEIN, ('HGNC', 'TMPRSS2'), ('p', 1, 79), ('HGNC', 'ERG'), ('p', 312, 5034)),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: INCREASES}),
            ((PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Arg1851*')),
             (PROTEIN, ('HGNC', 'BCR'), ('p', '?', 1875), ('HGNC', 'JAK2'), ('p', 2626, '?')),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: INCREASES}),
            ((PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.40*')),
             (PROTEIN, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: INCREASES}),
            ((PROTEIN, 'HGNC', 'CFTR', (HGVS, '=')), (PROTEIN, 'HGNC', 'EGFR'), {
                EVIDENCE: 'These are mostly made up',
                CITATION: citation_1,
                RELATION: INCREASES,
                OBJECT: {
                    MODIFIER: TRANSLOCATION,
                    EFFECT: {FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'intracellular'},
                             TO_LOC: {NAMESPACE: 'GOCC', NAME: 'cell surface'}}}}),
            ((PROTEIN, 'HGNC', 'CFTR'), (PROTEIN, 'HGNC', 'CFTR', (HGVS, '=')), {RELATION: HAS_VARIANT}),
            ((PROTEIN, 'HGNC', 'CFTR'), (PROTEIN, 'HGNC', 'CFTR', (HGVS, '?')), {RELATION: HAS_VARIANT}),
            ((PROTEIN, 'HGNC', 'CFTR'), (PROTEIN, 'HGNC', 'CFTR', (HGVS, 'p.Phe508del')),
             {RELATION: HAS_VARIANT}),
            ((PROTEIN, 'HGNC', 'CFTR'), (PROTEIN, 'HGNC', 'CFTR', (HGVS, 'p.Gly576Ala')),
             {RELATION: HAS_VARIANT}),
            ((PROTEIN, 'HGNC', 'CFTR', (HGVS, '?')), (PATHOLOGY, 'MESHD', 'Adenocarcinoma'),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: INCREASES}),
            ((PROTEIN, 'HGNC', 'MIA', (FRAGMENT, (5, 20))), (COMPLEX, 'GOCC', 'interleukin-23 complex'),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: INCREASES,
              OBJECT: {
                  MODIFIER: TRANSLOCATION,
                  EFFECT: {FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'intracellular'},
                           TO_LOC: {NAMESPACE: 'GOCC',
                                    NAME: 'extracellular space'}}}}),
            ((PROTEIN, 'HGNC', 'MIA'), (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, (5, 20))), {RELATION: HAS_VARIANT}),
            ((PROTEIN, 'HGNC', 'MIA'), (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, (1, '?'))), {RELATION: HAS_VARIANT}),
            ((PROTEIN, 'HGNC', 'MIA'), (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, '?')), {RELATION: HAS_VARIANT}),
            ((PROTEIN, 'HGNC', 'MIA'), (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, '?', '55kD')), {RELATION: HAS_VARIANT}),
            ((PROTEIN, 'HGNC', 'MIA', (FRAGMENT, (1, '?'))), (PROTEIN, 'HGNC', 'EGFR'), {
                EVIDENCE: 'These are mostly made up',
                CITATION: citation_1,
                RELATION: INCREASES,
                OBJECT: {
                    MODIFIER: TRANSLOCATION,
                    EFFECT: {FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'cell surface'},
                             TO_LOC: {NAMESPACE: 'GOCC', NAME: 'endosome'}}}}),
            ((RNA, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'EGFR'), {
                EVIDENCE: 'These are mostly made up',
                CITATION: citation_1,
                RELATION: INCREASES,
                OBJECT: {MODIFIER: TRANSLOCATION, EFFECT: {
                    FROM_LOC: {NAMESPACE: 'GOCC',
                               NAME: 'cell surface'},
                    TO_LOC: {NAMESPACE: 'GOCC',
                             NAME: 'endosome'}}}}),
            ((RNA, 'HGNC', 'AKT1'), (RNA, 'HGNC', 'AKT1', (HGVS, 'c.1521_1523delCTT'), (HGVS, 'p.Phe508del')),
             {RELATION: HAS_VARIANT}),
            ((RNA, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1'),
             {EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
              CITATION: citation_2,
              RELATION: 'translatedTo'}),
            ((RNA, 'HGNC', 'AKT1', (HGVS, 'c.1521_1523delCTT'), (HGVS, 'p.Phe508del')),
             (RNA, ('HGNC', 'TMPRSS2'), ('r', 1, 79), ('HGNC', 'ERG'), ('r', 312, 5034)),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: 'directlyIncreases'}),
            ((RNA, ('HGNC', 'TMPRSS2'), ('?',), ('HGNC', 'ERG'), ('?',)),
             (COMPLEX, (GENE, 'HGNC', 'NCF1'), (PROTEIN, 'HGNC', 'HBP1')),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: INCREASES}),
            ((COMPLEX, (GENE, 'HGNC', 'NCF1'), (PROTEIN, 'HGNC', 'HBP1')), (PROTEIN, 'HGNC', 'HBP1'),
             {RELATION: HAS_COMPONENT}),
            ((COMPLEX, (GENE, 'HGNC', 'NCF1'), (PROTEIN, 'HGNC', 'HBP1')), (GENE, 'HGNC', 'NCF1'),
             {RELATION: HAS_COMPONENT}),
            ((RNA, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
             (COMPLEX, (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')),
             {EVIDENCE: 'These are mostly made up',
              CITATION: citation_1,
              RELATION: INCREASES}),
            ((COMPLEX, (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')), (PROTEIN, 'HGNC', 'FOS'),
             {RELATION: HAS_COMPONENT}),
            ((COMPLEX, (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')), (PROTEIN, 'HGNC', 'JUN'),
             {RELATION: HAS_COMPONENT}),
            ((RNA, 'HGNC', 'CFTR'), (RNA, 'HGNC', 'CFTR', (HGVS, 'r.1521_1523delcuu')),
             {RELATION: HAS_VARIANT}),
            ((RNA, 'HGNC', 'CFTR'), (RNA, 'HGNC', 'CFTR', (HGVS, 'r.1653_1655delcuu')),
             {RELATION: HAS_VARIANT}),
            ((COMPOSITE, (COMPLEX, 'GOCC', 'interleukin-23 complex'), (PROTEIN, 'HGNC', 'IL6')),
             (PROTEIN, 'HGNC', 'IL6'), {RELATION: HAS_COMPONENT}),
            ((COMPOSITE, (COMPLEX, 'GOCC', 'interleukin-23 complex'), (PROTEIN, 'HGNC', 'IL6')),
             (COMPLEX, 'GOCC', 'interleukin-23 complex'), {RELATION: HAS_COMPONENT}),
            ((COMPOSITE, (COMPLEX, 'GOCC', 'interleukin-23 complex'), (PROTEIN, 'HGNC', 'IL6')),
             (BIOPROCESS, 'GOBP', 'cell cycle arrest'), {
                 EVIDENCE: 'These are mostly made up',
                 CITATION: citation_1,
                 RELATION: DECREASES}),
            ((REACTION, ((ABUNDANCE, ('CHEBI', 'superoxide')),),
              ((ABUNDANCE, ('CHEBI', 'dioxygen')), (ABUNDANCE, ('CHEBI', 'hydrogen peroxide')))),
             (ABUNDANCE, 'CHEBI', 'superoxide'), {RELATION: HAS_REACTANT}),
            ((REACTION, ((ABUNDANCE, ('CHEBI', 'superoxide')),),
              ((ABUNDANCE, ('CHEBI', 'dioxygen')), (ABUNDANCE, ('CHEBI', 'hydrogen peroxide')))),
             (ABUNDANCE, 'CHEBI', 'hydrogen peroxide'), {RELATION: HAS_PRODUCT}),
            ((REACTION, ((ABUNDANCE, ('CHEBI', 'superoxide')),),
              ((ABUNDANCE, ('CHEBI', 'dioxygen')), (ABUNDANCE, ('CHEBI', 'hydrogen peroxide')))),
             (ABUNDANCE, 'CHEBI', 'dioxygen'), {RELATION: HAS_PRODUCT}),
            ((PROTEIN, 'HGNC', 'CAT'), (ABUNDANCE, 'CHEBI', 'hydrogen peroxide'),
             {EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
              CITATION: citation_2,
              RELATION: 'directlyDecreases',
              SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}}}),
            ((GENE, 'HGNC', 'CAT'), (ABUNDANCE, 'CHEBI', 'hydrogen peroxide'), {
                EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
                CITATION: citation_2,
                RELATION: 'directlyDecreases',
                SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}}}),
            ((PROTEIN, 'HGNC', 'HMGCR'), (BIOPROCESS, 'GOBP', 'cholesterol biosynthetic process'), {
                EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
                CITATION: citation_2,
                RELATION: 'rateLimitingStepOf',
                SUBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAMESPACE: PYBEL_DEFAULT_NAMESPACE, NAME: 'cat'}}}),
            ((GENE, 'HGNC', 'APP', (HGVS, 'c.275341G>C')), (PATHOLOGY, 'MESHD', 'Alzheimer Disease'),
             {EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
              CITATION: citation_2,
              RELATION: 'causesNoChange'}),
            ((GENE, 'HGNC', 'APP'), (GENE, 'HGNC', 'APP', (HGVS, 'c.275341G>C')), {RELATION: HAS_VARIANT}),
            ((COMPLEX, (PROTEIN, 'HGNC', 'F3'), (PROTEIN, 'HGNC', 'F7')), (PROTEIN, 'HGNC', 'F3'),
             {RELATION: HAS_COMPONENT}),
            ((COMPLEX, (PROTEIN, 'HGNC', 'F3'), (PROTEIN, 'HGNC', 'F7')), (PROTEIN, 'HGNC', 'F7'),
             {RELATION: HAS_COMPONENT}),
            ((COMPLEX, (PROTEIN, 'HGNC', 'F3'), (PROTEIN, 'HGNC', 'F7')), (PROTEIN, 'HGNC', 'F9'),
             {EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
              CITATION: citation_2,
              RELATION: 'regulates',
              SUBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAME: 'pep', NAMESPACE: PYBEL_DEFAULT_NAMESPACE}},
              OBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAME: 'pep', NAMESPACE: PYBEL_DEFAULT_NAMESPACE}}}),
            ((PROTEIN, 'HGNC', 'GSK3B', (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 9)), (PROTEIN, 'HGNC', 'GSK3B'),
             {EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
              CITATION: citation_2,
              RELATION: 'positiveCorrelation',
              OBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAMESPACE: PYBEL_DEFAULT_NAMESPACE, NAME: 'kin'}}}),
            ((PROTEIN, 'HGNC', 'GSK3B'), (PROTEIN, 'HGNC', 'GSK3B', (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 9)),
             {RELATION: HAS_VARIANT}),
            ((PROTEIN, 'HGNC', 'GSK3B'), (PROTEIN, 'HGNC', 'GSK3B', (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 9)),
             {EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
              CITATION: citation_2,
              RELATION: 'positiveCorrelation',
              SUBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAMESPACE: PYBEL_DEFAULT_NAMESPACE, NAME: 'kin'}}}),
            ((PATHOLOGY, 'MESHD', 'Psoriasis'), (PATHOLOGY, 'MESHD', 'Skin Diseases'),
             {EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
              CITATION: citation_2,
              RELATION: 'isA'}),
            ((REACTION, (
                (ABUNDANCE, ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), (ABUNDANCE, ('CHEBI', 'NADPH')),
                (ABUNDANCE, ('CHEBI', 'hydron'))),
              ((ABUNDANCE, ('CHEBI', 'NADP(+)')), (ABUNDANCE, ('CHEBI', 'mevalonate')))),
             (ABUNDANCE, 'CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'), {RELATION: HAS_REACTANT}),
            ((REACTION, (
                (ABUNDANCE, ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), (ABUNDANCE, ('CHEBI', 'NADPH')),
                (ABUNDANCE, ('CHEBI', 'hydron'))),
              ((ABUNDANCE, ('CHEBI', 'NADP(+)')), (ABUNDANCE, ('CHEBI', 'mevalonate')))),
             (ABUNDANCE, 'CHEBI', 'NADPH'), {RELATION: HAS_REACTANT}),
            ((REACTION, (
                (ABUNDANCE, ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), (ABUNDANCE, ('CHEBI', 'NADPH')),
                (ABUNDANCE, ('CHEBI', 'hydron'))),
              ((ABUNDANCE, ('CHEBI', 'NADP(+)')), (ABUNDANCE, ('CHEBI', 'mevalonate')))),
             (ABUNDANCE, 'CHEBI', 'hydron'), {RELATION: HAS_REACTANT}),
            ((REACTION, (
                (ABUNDANCE, ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), (ABUNDANCE, ('CHEBI', 'NADPH')),
                (ABUNDANCE, ('CHEBI', 'hydron'))),
              ((ABUNDANCE, ('CHEBI', 'NADP(+)')), (ABUNDANCE, ('CHEBI', 'mevalonate')))),
             (ABUNDANCE, 'CHEBI', 'mevalonate'), {RELATION: HAS_PRODUCT}),
            ((REACTION, (
                (ABUNDANCE, ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), (ABUNDANCE, ('CHEBI', 'NADPH')),
                (ABUNDANCE, ('CHEBI', 'hydron'))),
              ((ABUNDANCE, ('CHEBI', 'NADP(+)')), (ABUNDANCE, ('CHEBI', 'mevalonate')))),
             (ABUNDANCE, 'CHEBI', 'NADP(+)'), {RELATION: HAS_PRODUCT}),
            ((REACTION, (
                (ABUNDANCE, ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), (ABUNDANCE, ('CHEBI', 'NADPH')),
                (ABUNDANCE, ('CHEBI', 'hydron'))),
              ((ABUNDANCE, ('CHEBI', 'NADP(+)')), (ABUNDANCE, ('CHEBI', 'mevalonate')))),
             (BIOPROCESS, 'GOBP', 'cholesterol biosynthetic process'),
             {EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
              CITATION: citation_2,
              RELATION: 'subProcessOf'}),
            ((ABUNDANCE, 'CHEBI', 'nitric oxide'),
             (COMPLEX, (PROTEIN, 'HGNC', 'ITGAV'), (PROTEIN, 'HGNC', 'ITGB3')), {
                 EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
                 CITATION: citation_2,
                 RELATION: INCREASES,
                 OBJECT: {
                     MODIFIER: TRANSLOCATION,
                     EFFECT: {FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'intracellular'},
                              TO_LOC: {NAMESPACE: 'GOCC', NAME: 'cell surface'}}}}),
            ((COMPLEX, (PROTEIN, 'HGNC', 'ITGAV'), (PROTEIN, 'HGNC', 'ITGB3')), (PROTEIN, 'HGNC', 'ITGAV'),
             {RELATION: HAS_COMPONENT}),
            ((COMPLEX, (PROTEIN, 'HGNC', 'ITGAV'), (PROTEIN, 'HGNC', 'ITGB3')), (PROTEIN, 'HGNC', 'ITGB3'),
             {RELATION: HAS_COMPONENT}),
            ((GENE, 'HGNC', 'ARRDC2'), (GENE, 'HGNC', 'ARRDC3'), {RELATION: EQUIVALENT_TO}),
            ((GENE, 'HGNC', 'ARRDC3'), (GENE, 'HGNC', 'ARRDC2'), {RELATION: EQUIVALENT_TO}),
            ((GENE, 'dbSNP', 'rs123456'), (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')), {RELATION: ASSOCIATION}),
            ((GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')), (GENE, 'dbSNP', 'rs123456'), {RELATION: ASSOCIATION}),
        ]

        # FIXME
        # self.assertEqual(set((u, v) for u, v, _ in e), set(g.edges()))

        for u, v, d in e:
            assertHasEdge(self, u, v, g, **d)
