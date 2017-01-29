# -*- coding: utf-8 -*-

import logging
import os
import unittest

import networkx as nx
import ontospy
from requests.compat import urlparse

from pybel import BELGraph
from pybel.constants import FUNCTION, NAMESPACE, NAME
from pybel.constants import PROTEIN, ABUNDANCE, GENE, RNA, PROTEIN_FUSION, GENE_FUSION, RNA_FUSION, MIRNA, COMPLEX, \
    COMPOSITE, BIOPROCESS, PATHOLOGY, REACTION, PMOD, HGVS, GMOD, PYBEL_DEFAULT_NAMESPACE
from pybel.manager.utils import urldefrag, OWLParser
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

test_citation_dict = dict(type='PubMed', name='TestName', reference='1235813')
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
        msg_format = 'No edge ({}, {}) with correct properties. expected {} but got {}'
        self.assertTrue(any_subdict_matches(graph.edge[u][v], kwargs),
                        msg=msg_format.format(u, v, kwargs, graph.edge[u][v]))


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


def parse_owl_ontospy_resolver(iri):
    path = os.path.join(owl_dir_path, get_uri_name(iri))
    o = ontospy.Ontospy(path)

    g = nx.DiGraph(IRI=iri)

    for cls in o.classes:
        g.add_node(cls.locale, type='Class')

        for parent in cls.parents():
            g.add_edge(cls.locale, parent.locale, type='SubClassOf')

        for instance in cls.instances():
            _, frag = urldefrag(instance)
            g.add_edge(frag, cls.locale, type='ClassAssertion')

    return g


mock_parse_owl_ontospy = mock.patch('pybel.manager.utils.parse_owl_ontospy', side_effect=parse_owl_ontospy_resolver)


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

        assertHasEdge(self, AKT1, EGFR, g, relation='increases', TESTAN1="1")
        assertHasEdge(self, EGFR, FADD, g, relation='decreases', TESTAN1="1", TESTAN2="3")
        assertHasEdge(self, EGFR, CASP8, g, relation='directlyDecreases', TESTAN1="1", TESTAN2="3")
        assertHasEdge(self, FADD, CASP8, g, relation='increases', TESTAN1="2")
        assertHasEdge(self, AKT1, CASP8, g, relation='association', TESTAN1="2")

    def bel_thorough_reconstituted(self, g, check_metadata=True):
        self.assertIsNotNone(g)
        self.assertIsInstance(g, BELGraph)
        self.assertEqual(0, len(g.warnings), msg='Document warnings:\n{}'.format('\n'.join(map(str, g.warnings))))

        x = {
            (ABUNDANCE, 'CHEBI', 'oxygen atom'),
            (GENE, 'HGNC', 'AKT1', (GMOD, (PYBEL_DEFAULT_NAMESPACE, 'Me'))),
            (GENE, 'HGNC', 'AKT1'),
            (GENE, 'HGNC', 'AKT1', (HGVS, 'p.Phe508del')),
            (PROTEIN, 'HGNC', 'AKT1'),
            (GENE, 'HGNC', 'AKT1', (HGVS, 'g.308G>A')),
            (GENE_FUSION, ('HGNC', 'TMPRSS2'), ('c', 1, 79), ('HGNC', 'ERG'), ('c', 312, 5034)),
            (GENE, 'HGNC', 'AKT1', (HGVS, 'delCTT'), (HGVS, 'g.308G>A'), (HGVS, 'p.Phe508del')),
            (MIRNA, 'HGNC', 'MIR21'),
            (GENE_FUSION, ('HGNC', 'BCR'), ('c', '?', 1875), ('HGNC', 'JAK2'), ('c', 2626, '?')),
            (GENE, 'HGNC', 'CFTR', (HGVS, 'delCTT')),
            (GENE, 'HGNC', 'CFTR'),
            (GENE, 'HGNC', 'CFTR', (HGVS, 'g.117199646_117199648delCTT')),
            (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')),
            (PROTEIN, 'HGNC', 'AKT1', (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 473)),
            (MIRNA, 'HGNC', 'MIR21', (HGVS, 'p.Phe508del')),
            (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.C40*')),
            (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Ala127Tyr'), (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser')),
            (GENE_FUSION, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
            (PROTEIN_FUSION, ('HGNC', 'TMPRSS2'), ('p', 1, 79), ('HGNC', 'ERG'), ('p', 312, 5034)),
            (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Arg1851*')),
            (PROTEIN_FUSION, ('HGNC', 'BCR'), ('p', '?', 1875), ('HGNC', 'JAK2'), ('p', 2626, '?')),
            (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.40*')),
            (PROTEIN_FUSION, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
            (PROTEIN, 'HGNC', 'CFTR', (HGVS, '=')),
            (PROTEIN, 'HGNC', 'CFTR'),
            (PROTEIN, 'HGNC', 'EGFR'),
            (PROTEIN, 'HGNC', 'CFTR', (HGVS, '?')),
            (PATHOLOGY, 'MESHD', 'Adenocarcinoma'),
            (PROTEIN, 'HGNC', 'CFTR', (HGVS, 'p.Phe508del')),
            (PROTEIN, 'HGNC', 'MIA', ('frag', (5, 20))),
            (PROTEIN, 'HGNC', 'MIA'),
            (COMPLEX, 'GOCC', 'interleukin-23 complex'),
            (PROTEIN, 'HGNC', 'MIA', ('frag', (1, '?'))),
            (PROTEIN, 'HGNC', 'MIA', ('frag', '?')),
            (PROTEIN, 'HGNC', 'MIA', ('frag', '?', '55kD')),
            (PROTEIN, 'HGNC', 'CFTR', (HGVS, 'p.Gly576Ala')),
            (RNA, 'HGNC', 'AKT1'),
            (RNA, 'HGNC', 'AKT1', (HGVS, 'delCTT'), (HGVS, 'p.Phe508del')),
            (RNA_FUSION, ('HGNC', 'TMPRSS2'), ('r', 1, 79), ('HGNC', 'ERG'), ('r', 312, 5034)),
            (RNA_FUSION, ('HGNC', 'TMPRSS2'), ('?',), ('HGNC', 'ERG'), ('?',)),
            (COMPLEX, (GENE, 'HGNC', 'NCF1'), (PROTEIN, 'HGNC', 'HBP1')),
            (PROTEIN, 'HGNC', 'HBP1'),
            (GENE, 'HGNC', 'NCF1'),
            (RNA_FUSION, ('HGNC', 'BCR'), ('r', '?', 1875), ('HGNC', 'JAK2'), ('r', 2626, '?')),
            (RNA_FUSION, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
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
            (GENE, 'HGNC', 'APP', (HGVS, 'g.275341G>C')),
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
            (PROTEIN, 'HGNC', 'MAPT')
        }

        self.assertEqual(x, set(g.nodes()))

        citation_1 = {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'}
        citation_2 = {'type': 'PubMed', 'name': 'That one article from last week #2', 'reference': '123456'}

        e = [
            ((ABUNDANCE, 'CHEBI', 'oxygen atom'), (GENE, 'HGNC', 'AKT1', (GMOD, (PYBEL_DEFAULT_NAMESPACE, 'Me'))),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'increases'}),
            ((GENE, 'HGNC', 'AKT1'), (GENE, 'HGNC', 'AKT1', (GMOD, (PYBEL_DEFAULT_NAMESPACE, 'Me'))),
             {'relation': 'hasVariant'}),
            ((GENE, 'HGNC', 'AKT1'), (ABUNDANCE, 'CHEBI', 'oxygen atom'),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'decreases', 'subject': {'location': {'namespace': 'GOCC', 'name': 'intracellular'}},
              'object': {'location': {'namespace': 'GOCC', 'name': 'intracellular'}}}),
            ((GENE, 'HGNC', 'AKT1'), (GENE, 'HGNC', 'AKT1', (HGVS, 'p.Phe508del')), {'relation': 'hasVariant'}),
            ((GENE, 'HGNC', 'AKT1'), (GENE, 'HGNC', 'AKT1', (HGVS, 'g.308G>A')), {'relation': 'hasVariant'}),
            ((GENE, 'HGNC', 'AKT1'),
             (GENE, 'HGNC', 'AKT1', (HGVS, 'delCTT'), (HGVS, 'g.308G>A'), (HGVS, 'p.Phe508del')),
             {'relation': 'hasVariant'}),
            ((GENE, 'HGNC', 'AKT1'), (RNA, 'HGNC', 'AKT1'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': citation_2,
              'relation': 'transcribedTo'}),
            ((GENE, 'HGNC', 'AKT1', (HGVS, 'p.Phe508del')), (PROTEIN, 'HGNC', 'AKT1'),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'directlyDecreases'}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1', (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 473)),
             {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.C40*')), {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'AKT1'),
             (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Ala127Tyr'), (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser')),
             {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'AKT1'),
             (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Ala127Tyr'), (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser')),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'directlyDecreases', 'subject': {'location': {'namespace': 'GOCC', 'name': 'intracellular'}},
              'object': {'location': {'namespace': 'GOCC', 'name': 'intracellular'}}}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Arg1851*')),
             {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.40*')), {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'MIA', ('frag', '?')),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'increases', 'subject': {'modifier': 'Degradation'}}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'CFTR', (HGVS, 'p.Gly576Ala')),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'increases'}),
            ((PROTEIN, 'HGNC', 'AKT1'), (RNA, 'HGNC', 'CFTR', (HGVS, 'r.1521_1523delcuu')),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'increases',
              'subject': {'modifier': 'Activity', 'effect': {'namespace': PYBEL_DEFAULT_NAMESPACE, 'name': 'kin'}}}),
            ((PROTEIN, 'HGNC', 'AKT1'), (RNA, 'HGNC', 'CFTR', (HGVS, 'r.1653_1655delcuu')),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'increases', 'subject': {'modifier': 'Activity', 'effect': {}}}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'EGFR'), {
                'SupportingText': 'These are mostly made up',
                'citation': {'type': 'PubMed',
                             'name': 'That one article from last week',
                             'reference': '123455'},
                'relation': 'increases',
                'subject': {'modifier': 'Activity',
                            'effect': {'namespace': PYBEL_DEFAULT_NAMESPACE,
                                       'name': 'cat'}},
                'object': {'modifier': 'Degradation'}}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'EGFR'), {
                'SupportingText': 'These are mostly made up',
                'citation': {'type': 'PubMed',
                             'name': 'That one article from last week',
                             'reference': '123455'},
                'relation': 'increases',
                'subject': {'modifier': 'Activity',
                            'effect': {'name': 'kin',
                                       'namespace': PYBEL_DEFAULT_NAMESPACE}},
                'object': {'modifier': 'Translocation',
                           'effect': {
                               'fromLoc': {'namespace': 'GOCC',
                                           'name': 'intracellular'},
                               'toLoc': {'namespace': 'GOCC',
                                         'name': 'extracellular space'}}}}),
            ((GENE, 'HGNC', 'AKT1', (HGVS, 'g.308G>A')),
             (GENE_FUSION, ('HGNC', 'TMPRSS2'), ('c', 1, 79), ('HGNC', 'ERG'), ('c', 312, 5034)),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'causesNoChange'}),
            ((GENE, 'HGNC', 'AKT1', (HGVS, 'g.308G>A')),
             (GENE, 'HGNC', 'AKT1', (HGVS, 'delCTT'), (HGVS, 'g.308G>A'), (HGVS, 'p.Phe508del')),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'increases', 'subject': {'location': {'namespace': 'GOCC', 'name': 'intracellular'}}}),
            ((MIRNA, 'HGNC', 'MIR21'),
             (GENE_FUSION, ('HGNC', 'BCR'), ('c', '?', 1875), ('HGNC', 'JAK2'), ('c', 2626, '?')),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'directlyIncreases'}),
            ((MIRNA, 'HGNC', 'MIR21'), (PROTEIN, 'HGNC', 'AKT1', (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 473)),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'decreases', 'subject': {'location': {'namespace': 'GOCC', 'name': 'intracellular'}}}),
            ((MIRNA, 'HGNC', 'MIR21'), (MIRNA, 'HGNC', 'MIR21', (HGVS, 'p.Phe508del')),
             {'relation': 'hasVariant'}),
            ((GENE, 'HGNC', 'CFTR', (HGVS, 'delCTT')), (PROTEIN, 'HGNC', 'AKT1'),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'increases', 'object': {'modifier': 'Degradation'}}),
            ((GENE, 'HGNC', 'CFTR'), (GENE, 'HGNC', 'CFTR', (HGVS, 'delCTT')), {'relation': 'hasVariant'}),
            ((GENE, 'HGNC', 'CFTR'), (GENE, 'HGNC', 'CFTR', (HGVS, 'g.117199646_117199648delCTT')),
             {'relation': 'hasVariant'}),
            ((GENE, 'HGNC', 'CFTR'), (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')),
             {'relation': 'hasVariant'}),
            ((GENE, 'HGNC', 'CFTR', (HGVS, 'g.117199646_117199648delCTT')),
             (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')), {
                 'SupportingText': 'These are mostly made up',
                 'citation': {'type': 'PubMed',
                              'name': 'That one article from last week',
                              'reference': '123455'},
                 'relation': 'increases'}),
            ((MIRNA, 'HGNC', 'MIR21', (HGVS, 'p.Phe508del')), (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.C40*')),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'increases', 'subject': {'location': {'namespace': 'GOCC', 'name': 'intracellular'}}}),
            ((GENE_FUSION, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
             (PROTEIN_FUSION, ('HGNC', 'TMPRSS2'), ('p', 1, 79), ('HGNC', 'ERG'), ('p', 312, 5034)),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'increases'}),
            ((PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Arg1851*')),
             (PROTEIN_FUSION, ('HGNC', 'BCR'), ('p', '?', 1875), ('HGNC', 'JAK2'), ('p', 2626, '?')),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'increases'}),
            ((PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.40*')),
             (PROTEIN_FUSION, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'increases'}),
            ((PROTEIN, 'HGNC', 'CFTR', (HGVS, '=')), (PROTEIN, 'HGNC', 'EGFR'),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'increases', 'object': {'modifier': 'Translocation',
                                                  'effect': {'fromLoc': {'namespace': 'GOCC', 'name': 'intracellular'},
                                                             'toLoc': {'namespace': 'GOCC', 'name': 'cell surface'}}}}),
            ((PROTEIN, 'HGNC', 'CFTR'), (PROTEIN, 'HGNC', 'CFTR', (HGVS, '=')), {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'CFTR'), (PROTEIN, 'HGNC', 'CFTR', (HGVS, '?')), {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'CFTR'), (PROTEIN, 'HGNC', 'CFTR', (HGVS, 'p.Phe508del')),
             {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'CFTR'), (PROTEIN, 'HGNC', 'CFTR', (HGVS, 'p.Gly576Ala')),
             {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'CFTR', (HGVS, '?')), (PATHOLOGY, 'MESHD', 'Adenocarcinoma'),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'increases'}),
            ((PROTEIN, 'HGNC', 'MIA', ('frag', (5, 20))), (COMPLEX, 'GOCC', 'interleukin-23 complex'),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'increases', 'object': {'modifier': 'Translocation',
                                                  'effect': {'fromLoc': {'namespace': 'GOCC', 'name': 'intracellular'},
                                                             'toLoc': {'namespace': 'GOCC',
                                                                       'name': 'extracellular space'}}}}),
            ((PROTEIN, 'HGNC', 'MIA'), (PROTEIN, 'HGNC', 'MIA', ('frag', (5, 20))), {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'MIA'), (PROTEIN, 'HGNC', 'MIA', ('frag', (1, '?'))), {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'MIA'), (PROTEIN, 'HGNC', 'MIA', ('frag', '?')), {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'MIA'), (PROTEIN, 'HGNC', 'MIA', ('frag', '?', '55kD')), {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'MIA', ('frag', (1, '?'))), (PROTEIN, 'HGNC', 'EGFR'),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'increases', 'object': {'modifier': 'Translocation',
                                                  'effect': {'fromLoc': {'namespace': 'GOCC', 'name': 'cell surface'},
                                                             'toLoc': {'namespace': 'GOCC', 'name': 'endosome'}}}}),
            ((RNA, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'EGFR'), {'SupportingText': 'These are mostly made up',
                                                                'citation': {'type': 'PubMed',
                                                                             'name': 'That one article from last week',
                                                                             'reference': '123455'},
                                                                'relation': 'increases',
                                                                'object': {'modifier': 'Translocation', 'effect': {
                                                                    'fromLoc': {'namespace': 'GOCC',
                                                                                'name': 'cell surface'},
                                                                    'toLoc': {'namespace': 'GOCC',
                                                                              'name': 'endosome'}}}}),
            ((RNA, 'HGNC', 'AKT1'), (RNA, 'HGNC', 'AKT1', (HGVS, 'delCTT'), (HGVS, 'p.Phe508del')),
             {'relation': 'hasVariant'}),
            ((RNA, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': citation_2,
              'relation': 'translatedTo'}),
            ((RNA, 'HGNC', 'AKT1', (HGVS, 'delCTT'), (HGVS, 'p.Phe508del')),
             (RNA_FUSION, ('HGNC', 'TMPRSS2'), ('r', 1, 79), ('HGNC', 'ERG'), ('r', 312, 5034)),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'directlyIncreases'}),
            ((RNA_FUSION, ('HGNC', 'TMPRSS2'), ('?',), ('HGNC', 'ERG'), ('?',)),
             (COMPLEX, (GENE, 'HGNC', 'NCF1'), (PROTEIN, 'HGNC', 'HBP1')),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'increases'}),
            ((COMPLEX, (GENE, 'HGNC', 'NCF1'), (PROTEIN, 'HGNC', 'HBP1')), (PROTEIN, 'HGNC', 'HBP1'),
             {'relation': 'hasComponent'}),
            ((COMPLEX, (GENE, 'HGNC', 'NCF1'), (PROTEIN, 'HGNC', 'HBP1')), (GENE, 'HGNC', 'NCF1'),
             {'relation': 'hasComponent'}),
            ((RNA_FUSION, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
             (COMPLEX, (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')),
             {'SupportingText': 'These are mostly made up',
              'citation': citation_1,
              'relation': 'increases'}),
            ((COMPLEX, (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')), (PROTEIN, 'HGNC', 'FOS'),
             {'relation': 'hasComponent'}),
            ((COMPLEX, (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')), (PROTEIN, 'HGNC', 'JUN'),
             {'relation': 'hasComponent'}),
            ((RNA, 'HGNC', 'CFTR'), (RNA, 'HGNC', 'CFTR', (HGVS, 'r.1521_1523delcuu')),
             {'relation': 'hasVariant'}),
            ((RNA, 'HGNC', 'CFTR'), (RNA, 'HGNC', 'CFTR', (HGVS, 'r.1653_1655delcuu')),
             {'relation': 'hasVariant'}),
            ((COMPOSITE, (COMPLEX, 'GOCC', 'interleukin-23 complex'), (PROTEIN, 'HGNC', 'IL6')),
             (PROTEIN, 'HGNC', 'IL6'), {'relation': 'hasComponent'}),
            ((COMPOSITE, (COMPLEX, 'GOCC', 'interleukin-23 complex'), (PROTEIN, 'HGNC', 'IL6')),
             (COMPLEX, 'GOCC', 'interleukin-23 complex'), {'relation': 'hasComponent'}),
            ((COMPOSITE, (COMPLEX, 'GOCC', 'interleukin-23 complex'), (PROTEIN, 'HGNC', 'IL6')),
             (BIOPROCESS, 'GOBP', 'cell cycle arrest'), {'SupportingText': 'These are mostly made up',
                                                         'citation': {'type': 'PubMed',
                                                                      'name': 'That one article from last week',
                                                                      'reference': '123455'},
                                                         'relation': 'decreases'}),
            ((REACTION, ((ABUNDANCE, ('CHEBI', 'superoxide')),),
              ((ABUNDANCE, ('CHEBI', 'dioxygen')), (ABUNDANCE, ('CHEBI', 'hydrogen peroxide')))),
             (ABUNDANCE, 'CHEBI', 'superoxide'), {'relation': 'hasReactant'}),
            ((REACTION, ((ABUNDANCE, ('CHEBI', 'superoxide')),),
              ((ABUNDANCE, ('CHEBI', 'dioxygen')), (ABUNDANCE, ('CHEBI', 'hydrogen peroxide')))),
             (ABUNDANCE, 'CHEBI', 'hydrogen peroxide'), {'relation': 'hasProduct'}),
            ((REACTION, ((ABUNDANCE, ('CHEBI', 'superoxide')),),
              ((ABUNDANCE, ('CHEBI', 'dioxygen')), (ABUNDANCE, ('CHEBI', 'hydrogen peroxide')))),
             (ABUNDANCE, 'CHEBI', 'dioxygen'), {'relation': 'hasProduct'}),
            ((PROTEIN, 'HGNC', 'CAT'), (ABUNDANCE, 'CHEBI', 'hydrogen peroxide'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': citation_2,
              'relation': 'directlyDecreases',
              'subject': {'location': {'namespace': 'GOCC', 'name': 'intracellular'}}}),
            ((GENE, 'HGNC', 'CAT'), (ABUNDANCE, 'CHEBI', 'hydrogen peroxide'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': citation_2,
              'relation': 'directlyDecreases',
              'subject': {'location': {'namespace': 'GOCC', 'name': 'intracellular'}}}),
            ((PROTEIN, 'HGNC', 'HMGCR'), (BIOPROCESS, 'GOBP', 'cholesterol biosynthetic process'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': citation_2,
              'relation': 'rateLimitingStepOf',
              'subject': {'modifier': 'Activity', 'effect': {'namespace': PYBEL_DEFAULT_NAMESPACE, 'name': 'cat'}}}),
            ((GENE, 'HGNC', 'APP', (HGVS, 'g.275341G>C')), (PATHOLOGY, 'MESHD', 'Alzheimer Disease'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': citation_2,
              'relation': 'causesNoChange'}),
            ((GENE, 'HGNC', 'APP'), (GENE, 'HGNC', 'APP', (HGVS, 'g.275341G>C')), {'relation': 'hasVariant'}),
            ((COMPLEX, (PROTEIN, 'HGNC', 'F3'), (PROTEIN, 'HGNC', 'F7')), (PROTEIN, 'HGNC', 'F3'),
             {'relation': 'hasComponent'}),
            ((COMPLEX, (PROTEIN, 'HGNC', 'F3'), (PROTEIN, 'HGNC', 'F7')), (PROTEIN, 'HGNC', 'F7'),
             {'relation': 'hasComponent'}),
            ((COMPLEX, (PROTEIN, 'HGNC', 'F3'), (PROTEIN, 'HGNC', 'F7')), (PROTEIN, 'HGNC', 'F9'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': citation_2,
              'relation': 'regulates',
              'subject': {'modifier': 'Activity', 'effect': {'name': 'pep', 'namespace': PYBEL_DEFAULT_NAMESPACE}},
              'object': {'modifier': 'Activity', 'effect': {'name': 'pep', 'namespace': PYBEL_DEFAULT_NAMESPACE}}}),
            ((PROTEIN, 'HGNC', 'GSK3B', (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 9)), (PROTEIN, 'HGNC', 'GSK3B'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': citation_2,
              'relation': 'positiveCorrelation',
              'object': {'modifier': 'Activity', 'effect': {'namespace': PYBEL_DEFAULT_NAMESPACE, 'name': 'kin'}}}),
            ((PROTEIN, 'HGNC', 'GSK3B'), (PROTEIN, 'HGNC', 'GSK3B', (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 9)),
             {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'GSK3B'), (PROTEIN, 'HGNC', 'GSK3B', (PMOD, (PYBEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 9)),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': citation_2,
              'relation': 'positiveCorrelation',
              'subject': {'modifier': 'Activity', 'effect': {'namespace': PYBEL_DEFAULT_NAMESPACE, 'name': 'kin'}}}),
            ((PATHOLOGY, 'MESHD', 'Psoriasis'), (PATHOLOGY, 'MESHD', 'Skin Diseases'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': citation_2,
              'relation': 'isA'}),
            ((REACTION, (
                (ABUNDANCE, ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), (ABUNDANCE, ('CHEBI', 'NADPH')),
                (ABUNDANCE, ('CHEBI', 'hydron'))),
              ((ABUNDANCE, ('CHEBI', 'NADP(+)')), (ABUNDANCE, ('CHEBI', 'mevalonate')))),
             (ABUNDANCE, 'CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'), {'relation': 'hasReactant'}),
            ((REACTION, (
                (ABUNDANCE, ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), (ABUNDANCE, ('CHEBI', 'NADPH')),
                (ABUNDANCE, ('CHEBI', 'hydron'))),
              ((ABUNDANCE, ('CHEBI', 'NADP(+)')), (ABUNDANCE, ('CHEBI', 'mevalonate')))),
             (ABUNDANCE, 'CHEBI', 'NADPH'), {'relation': 'hasReactant'}),
            ((REACTION, (
                (ABUNDANCE, ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), (ABUNDANCE, ('CHEBI', 'NADPH')),
                (ABUNDANCE, ('CHEBI', 'hydron'))),
              ((ABUNDANCE, ('CHEBI', 'NADP(+)')), (ABUNDANCE, ('CHEBI', 'mevalonate')))),
             (ABUNDANCE, 'CHEBI', 'hydron'), {'relation': 'hasReactant'}),
            ((REACTION, (
                (ABUNDANCE, ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), (ABUNDANCE, ('CHEBI', 'NADPH')),
                (ABUNDANCE, ('CHEBI', 'hydron'))),
              ((ABUNDANCE, ('CHEBI', 'NADP(+)')), (ABUNDANCE, ('CHEBI', 'mevalonate')))),
             (ABUNDANCE, 'CHEBI', 'mevalonate'), {'relation': 'hasProduct'}),
            ((REACTION, (
                (ABUNDANCE, ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), (ABUNDANCE, ('CHEBI', 'NADPH')),
                (ABUNDANCE, ('CHEBI', 'hydron'))),
              ((ABUNDANCE, ('CHEBI', 'NADP(+)')), (ABUNDANCE, ('CHEBI', 'mevalonate')))),
             (ABUNDANCE, 'CHEBI', 'NADP(+)'), {'relation': 'hasProduct'}),
            ((REACTION, (
                (ABUNDANCE, ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), (ABUNDANCE, ('CHEBI', 'NADPH')),
                (ABUNDANCE, ('CHEBI', 'hydron'))),
              ((ABUNDANCE, ('CHEBI', 'NADP(+)')), (ABUNDANCE, ('CHEBI', 'mevalonate')))),
             (BIOPROCESS, 'GOBP', 'cholesterol biosynthetic process'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': citation_2,
              'relation': 'subProcessOf'}),
            ((ABUNDANCE, 'CHEBI', 'nitric oxide'),
             (COMPLEX, (PROTEIN, 'HGNC', 'ITGAV'), (PROTEIN, 'HGNC', 'ITGB3')),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': citation_2,
              'relation': 'increases', 'object': {'modifier': 'Translocation',
                                                  'effect': {'fromLoc': {'namespace': 'GOCC', 'name': 'intracellular'},
                                                             'toLoc': {'namespace': 'GOCC', 'name': 'cell surface'}}}}),
            ((COMPLEX, (PROTEIN, 'HGNC', 'ITGAV'), (PROTEIN, 'HGNC', 'ITGB3')), (PROTEIN, 'HGNC', 'ITGAV'),
             {'relation': 'hasComponent'}),
            ((COMPLEX, (PROTEIN, 'HGNC', 'ITGAV'), (PROTEIN, 'HGNC', 'ITGB3')), (PROTEIN, 'HGNC', 'ITGB3'),
             {'relation': 'hasComponent'}),

        ]

        for u, v, d in e:
            assertHasEdge(self, u, v, g, **d)
