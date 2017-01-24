# -*- coding: utf-8 -*-

import logging
import os
import unittest

import networkx as nx
import ontospy
from requests.compat import urlparse

from pybel import BELGraph
from pybel.constants import FUNCTION, NAMESPACE, NAME
from pybel.manager.utils import urldefrag, OWLParser
from pybel.parser.parse_bel import BelParser
from pybel.parser.utils import any_subdict_matches

try:
    from unittest import mock
except ImportError:
    import mock

PROTEIN = 'Protein'

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

log = logging.getLogger('pybel')


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

        # assertHasNode(self, (), g)

        x = {
            ('Abundance', 'CHEBI', 'oxygen atom'),
            ('Gene', 'HGNC', 'AKT1', ('gmod', ('PYBEL', 'Me'))),
            ('Gene', 'HGNC', 'AKT1'),
            ('Gene', 'HGNC', 'AKT1', ('hgvs', 'p.Phe508del')),
            (PROTEIN, 'HGNC', 'AKT1'),
            ('Gene', 'HGNC', 'AKT1', ('hgvs', 'g.308G>A')),
            ('GeneFusion', ('HGNC', 'TMPRSS2'), ('c', 1, 79), ('HGNC', 'ERG'), ('c', 312, 5034)),
            ('Gene', 'HGNC', 'AKT1', ('hgvs', 'delCTT'), ('hgvs', 'g.308G>A'), ('hgvs', 'p.Phe508del')),
            ('miRNA', 'HGNC', 'MIR21'),
            ('GeneFusion', ('HGNC', 'BCR'), ('c', '?', 1875), ('HGNC', 'JAK2'), ('c', 2626, '?')),
            ('Gene', 'HGNC', 'CFTR', ('hgvs', 'delCTT')),
            ('Gene', 'HGNC', 'CFTR'),
            ('Gene', 'HGNC', 'CFTR', ('hgvs', 'g.117199646_117199648delCTT')),
            ('Gene', 'HGNC', 'CFTR', ('hgvs', 'c.1521_1523delCTT')),
            (PROTEIN, 'HGNC', 'AKT1', ('pmod', ('PYBEL', 'Ph'), 'Ser', 473)),
            ('miRNA', 'HGNC', 'MIR21', ('hgvs', 'p.Phe508del')),
            (PROTEIN, 'HGNC', 'AKT1', ('hgvs', 'p.C40*')),
            (PROTEIN, 'HGNC', 'AKT1', ('hgvs', 'p.Ala127Tyr'), ('pmod', ('PYBEL', 'Ph'), 'Ser')),
            ('GeneFusion', ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
            ('ProteinFusion', ('HGNC', 'TMPRSS2'), ('p', 1, 79), ('HGNC', 'ERG'), ('p', 312, 5034)),
            (PROTEIN, 'HGNC', 'AKT1', ('hgvs', 'p.Arg1851*')),
            ('ProteinFusion', ('HGNC', 'BCR'), ('p', '?', 1875), ('HGNC', 'JAK2'), ('p', 2626, '?')),
            (PROTEIN, 'HGNC', 'AKT1', ('hgvs', 'p.40*')),
            ('ProteinFusion', ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
            (PROTEIN, 'HGNC', 'CFTR', ('hgvs', '=')),
            (PROTEIN, 'HGNC', 'CFTR'),
            (PROTEIN, 'HGNC', 'EGFR'),
            (PROTEIN, 'HGNC', 'CFTR', ('hgvs', '?')),
            ('Pathology', 'MESHD', 'Adenocarcinoma'),
            (PROTEIN, 'HGNC', 'CFTR', ('hgvs', 'p.Phe508del')),
            (PROTEIN, 'HGNC', 'MIA', ('frag', (5, 20))),
            (PROTEIN, 'HGNC', 'MIA'),
            ('Complex', 'GOCC', 'interleukin-23 complex'),
            (PROTEIN, 'HGNC', 'MIA', ('frag', (1, '?'))),
            (PROTEIN, 'HGNC', 'MIA', ('frag', '?')),
            (PROTEIN, 'HGNC', 'MIA', ('frag', '?', '55kD')),
            (PROTEIN, 'HGNC', 'CFTR', ('hgvs', 'p.Gly576Ala')),
            ('RNA', 'HGNC', 'AKT1'),
            ('RNA', 'HGNC', 'AKT1', ('hgvs', 'delCTT'), ('hgvs', 'p.Phe508del')),
            ('RNAFusion', ('HGNC', 'TMPRSS2'), ('r', 1, 79), ('HGNC', 'ERG'), ('r', 312, 5034)),
            ('RNAFusion', ('HGNC', 'TMPRSS2'), ('?',), ('HGNC', 'ERG'), ('?',)),
            ('Complex', ('Gene', 'HGNC', 'NCF1'), (PROTEIN, 'HGNC', 'HBP1')),
            (PROTEIN, 'HGNC', 'HBP1'),
            ('Gene', 'HGNC', 'NCF1'),
            ('RNAFusion', ('HGNC', 'BCR'), ('r', '?', 1875), ('HGNC', 'JAK2'), ('r', 2626, '?')),
            ('RNAFusion', ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
            ('Complex', (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')),
            (PROTEIN, 'HGNC', 'FOS'),
            (PROTEIN, 'HGNC', 'JUN'),
            ('RNA', 'HGNC', 'CFTR', ('hgvs', 'r.1521_1523delcuu')),
            ('RNA', 'HGNC', 'CFTR'),
            ('RNA', 'HGNC', 'CFTR', ('hgvs', 'r.1653_1655delcuu')),
            ('Composite', ('Complex', 'GOCC', 'interleukin-23 complex'), (PROTEIN, 'HGNC', 'IL6')),
            (PROTEIN, 'HGNC', 'IL6'),
            ('BiologicalProcess', 'GOBP', 'cell cycle arrest'),
            ('Reaction', (('Abundance', ('CHEBI', 'superoxide')),),
             (('Abundance', ('CHEBI', 'dioxygen')), ('Abundance', ('CHEBI', 'hydrogen peroxide')))),
            ('Abundance', 'CHEBI', 'superoxide'),
            ('Abundance', 'CHEBI', 'hydrogen peroxide'),
            ('Abundance', 'CHEBI', 'dioxygen'),
            (PROTEIN, 'HGNC', 'CAT'),
            ('Gene', 'HGNC', 'CAT'),
            (PROTEIN, 'HGNC', 'HMGCR'),
            ('BiologicalProcess', 'GOBP', 'cholesterol biosynthetic process'),
            ('Gene', 'HGNC', 'APP', ('hgvs', 'g.275341G>C')),
            ('Gene', 'HGNC', 'APP'),
            ('Pathology', 'MESHD', 'Alzheimer Disease'),
            ('Complex', (PROTEIN, 'HGNC', 'F3'), (PROTEIN, 'HGNC', 'F7')),
            (PROTEIN, 'HGNC', 'F3'),
            (PROTEIN, 'HGNC', 'F7'),
            (PROTEIN, 'HGNC', 'F9'),
            (PROTEIN, 'HGNC', 'GSK3B', ('pmod', ('PYBEL', 'Ph'), 'Ser', 9)),
            (PROTEIN, 'HGNC', 'GSK3B'),
            ('Pathology', 'MESHD', 'Psoriasis'),
            ('Pathology', 'MESHD', 'Skin Diseases'),
            ('Reaction',
             (('Abundance', ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), ('Abundance', ('CHEBI', 'NADPH')),
              ('Abundance', ('CHEBI', 'hydron'))),
             (('Abundance', ('CHEBI', 'NADP(+)')), ('Abundance', ('CHEBI', 'mevalonate')))),
            ('Abundance', 'CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'),
            ('Abundance', 'CHEBI', 'NADPH'),
            ('Abundance', 'CHEBI', 'hydron'),
            ('Abundance', 'CHEBI', 'mevalonate'),
            ('Abundance', 'CHEBI', 'NADP(+)'),
            ('Abundance', 'CHEBI', 'nitric oxide'),
            ('Complex', (PROTEIN, 'HGNC', 'ITGAV'), (PROTEIN, 'HGNC', 'ITGB3')),
            (PROTEIN, 'HGNC', 'ITGAV'),
            (PROTEIN, 'HGNC', 'ITGB3')
        }

        self.assertEqual(x, set(g.nodes()))

        e = [
            (('Abundance', 'CHEBI', 'oxygen atom'), ('Gene', 'HGNC', 'AKT1', ('gmod', ('PYBEL', 'Me'))),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'increases'}),
            (('Gene', 'HGNC', 'AKT1'), ('Gene', 'HGNC', 'AKT1', ('gmod', ('PYBEL', 'Me'))), {'relation': 'hasVariant'}),
            (('Gene', 'HGNC', 'AKT1'), ('Abundance', 'CHEBI', 'oxygen atom'),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'decreases', 'subject': {'location': {'namespace': 'GOCC', 'name': 'intracellular'}},
              'object': {'location': {'namespace': 'GOCC', 'name': 'intracellular'}}}),
            (('Gene', 'HGNC', 'AKT1'), ('Gene', 'HGNC', 'AKT1', ('hgvs', 'p.Phe508del')), {'relation': 'hasVariant'}),
            (('Gene', 'HGNC', 'AKT1'), ('Gene', 'HGNC', 'AKT1', ('hgvs', 'g.308G>A')), {'relation': 'hasVariant'}),
            (('Gene', 'HGNC', 'AKT1'),
             ('Gene', 'HGNC', 'AKT1', ('hgvs', 'delCTT'), ('hgvs', 'g.308G>A'), ('hgvs', 'p.Phe508del')),
             {'relation': 'hasVariant'}),
            (('Gene', 'HGNC', 'AKT1'), ('RNA', 'HGNC', 'AKT1'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week #2', 'reference': '123456'},
              'relation': 'transcribedTo'}),
            (('Gene', 'HGNC', 'AKT1', ('hgvs', 'p.Phe508del')), (PROTEIN, 'HGNC', 'AKT1'),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'directlyDecreases'}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1', ('pmod', ('PYBEL', 'Ph'), 'Ser', 473)),
             {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1', ('hgvs', 'p.C40*')), {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'AKT1'),
             (PROTEIN, 'HGNC', 'AKT1', ('hgvs', 'p.Ala127Tyr'), ('pmod', ('PYBEL', 'Ph'), 'Ser')),
             {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'AKT1'),
             (PROTEIN, 'HGNC', 'AKT1', ('hgvs', 'p.Ala127Tyr'), ('pmod', ('PYBEL', 'Ph'), 'Ser')),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'directlyDecreases', 'subject': {'location': {'namespace': 'GOCC', 'name': 'intracellular'}},
              'object': {'location': {'namespace': 'GOCC', 'name': 'intracellular'}}}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1', ('hgvs', 'p.Arg1851*')),
             {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1', ('hgvs', 'p.40*')), {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'MIA', ('frag', '?')),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'increases', 'subject': {'modifier': 'Degradation'}}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'CFTR', ('hgvs', 'p.Gly576Ala')),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'increases'}),
            ((PROTEIN, 'HGNC', 'AKT1'), ('RNA', 'HGNC', 'CFTR', ('hgvs', 'r.1521_1523delcuu')),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'increases',
              'subject': {'modifier': 'Activity', 'effect': {'namespace': 'PYBEL', 'name': 'kin'}}}),
            ((PROTEIN, 'HGNC', 'AKT1'), ('RNA', 'HGNC', 'CFTR', ('hgvs', 'r.1653_1655delcuu')),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'increases', 'subject': {'modifier': 'Activity', 'effect': {}}}),
            ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'EGFR'), {
                'SupportingText': 'These are mostly made up',
                'citation': {'type': 'PubMed',
                             'name': 'That one article from last week',
                             'reference': '123455'},
                'relation': 'increases',
                'subject': {'modifier': 'Activity',
                            'effect': {'namespace': 'PYBEL',
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
                                       'namespace': 'PYBEL'}},
                'object': {'modifier': 'Translocation',
                           'effect': {
                               'fromLoc': {'namespace': 'GOCC',
                                           'name': 'intracellular'},
                               'toLoc': {'namespace': 'GOCC',
                                         'name': 'extracellular space'}}}}),
            (('Gene', 'HGNC', 'AKT1', ('hgvs', 'g.308G>A')),
             ('GeneFusion', ('HGNC', 'TMPRSS2'), ('c', 1, 79), ('HGNC', 'ERG'), ('c', 312, 5034)),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'causesNoChange'}),
            (('Gene', 'HGNC', 'AKT1', ('hgvs', 'g.308G>A')),
             ('Gene', 'HGNC', 'AKT1', ('hgvs', 'delCTT'), ('hgvs', 'g.308G>A'), ('hgvs', 'p.Phe508del')),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'increases', 'subject': {'location': {'namespace': 'GOCC', 'name': 'intracellular'}}}),
            (('miRNA', 'HGNC', 'MIR21'),
             ('GeneFusion', ('HGNC', 'BCR'), ('c', '?', 1875), ('HGNC', 'JAK2'), ('c', 2626, '?')),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'directlyIncreases'}),
            (('miRNA', 'HGNC', 'MIR21'), (PROTEIN, 'HGNC', 'AKT1', ('pmod', ('PYBEL', 'Ph'), 'Ser', 473)),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'decreases', 'subject': {'location': {'namespace': 'GOCC', 'name': 'intracellular'}}}),
            (('miRNA', 'HGNC', 'MIR21'), ('miRNA', 'HGNC', 'MIR21', ('hgvs', 'p.Phe508del')),
             {'relation': 'hasVariant'}),
            (('Gene', 'HGNC', 'CFTR', ('hgvs', 'delCTT')), (PROTEIN, 'HGNC', 'AKT1'),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'increases', 'object': {'modifier': 'Degradation'}}),
            (('Gene', 'HGNC', 'CFTR'), ('Gene', 'HGNC', 'CFTR', ('hgvs', 'delCTT')), {'relation': 'hasVariant'}),
            (('Gene', 'HGNC', 'CFTR'), ('Gene', 'HGNC', 'CFTR', ('hgvs', 'g.117199646_117199648delCTT')),
             {'relation': 'hasVariant'}),
            (('Gene', 'HGNC', 'CFTR'), ('Gene', 'HGNC', 'CFTR', ('hgvs', 'c.1521_1523delCTT')),
             {'relation': 'hasVariant'}),
            (('Gene', 'HGNC', 'CFTR', ('hgvs', 'g.117199646_117199648delCTT')),
             ('Gene', 'HGNC', 'CFTR', ('hgvs', 'c.1521_1523delCTT')), {
                 'SupportingText': 'These are mostly made up',
                 'citation': {'type': 'PubMed',
                              'name': 'That one article from last week',
                              'reference': '123455'},
                 'relation': 'increases'}),
            (('miRNA', 'HGNC', 'MIR21', ('hgvs', 'p.Phe508del')), (PROTEIN, 'HGNC', 'AKT1', ('hgvs', 'p.C40*')),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'increases', 'subject': {'location': {'namespace': 'GOCC', 'name': 'intracellular'}}}),
            (('GeneFusion', ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
             ('ProteinFusion', ('HGNC', 'TMPRSS2'), ('p', 1, 79), ('HGNC', 'ERG'), ('p', 312, 5034)),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'increases'}),
            ((PROTEIN, 'HGNC', 'AKT1', ('hgvs', 'p.Arg1851*')),
             ('ProteinFusion', ('HGNC', 'BCR'), ('p', '?', 1875), ('HGNC', 'JAK2'), ('p', 2626, '?')),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'increases'}),
            ((PROTEIN, 'HGNC', 'AKT1', ('hgvs', 'p.40*')),
             ('ProteinFusion', ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'increases'}),
            ((PROTEIN, 'HGNC', 'CFTR', ('hgvs', '=')), (PROTEIN, 'HGNC', 'EGFR'),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'increases', 'object': {'modifier': 'Translocation',
                                                  'effect': {'fromLoc': {'namespace': 'GOCC', 'name': 'intracellular'},
                                                             'toLoc': {'namespace': 'GOCC', 'name': 'cell surface'}}}}),
            ((PROTEIN, 'HGNC', 'CFTR'), (PROTEIN, 'HGNC', 'CFTR', ('hgvs', '=')), {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'CFTR'), (PROTEIN, 'HGNC', 'CFTR', ('hgvs', '?')), {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'CFTR'), (PROTEIN, 'HGNC', 'CFTR', ('hgvs', 'p.Phe508del')),
             {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'CFTR'), (PROTEIN, 'HGNC', 'CFTR', ('hgvs', 'p.Gly576Ala')),
             {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'CFTR', ('hgvs', '?')), ('Pathology', 'MESHD', 'Adenocarcinoma'),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'increases'}),
            ((PROTEIN, 'HGNC', 'MIA', ('frag', (5, 20))), ('Complex', 'GOCC', 'interleukin-23 complex'),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
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
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'increases', 'object': {'modifier': 'Translocation',
                                                  'effect': {'fromLoc': {'namespace': 'GOCC', 'name': 'cell surface'},
                                                             'toLoc': {'namespace': 'GOCC', 'name': 'endosome'}}}}),
            (('RNA', 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'EGFR'), {'SupportingText': 'These are mostly made up',
                                                                    'citation': {'type': 'PubMed',
                                                                                 'name': 'That one article from last week',
                                                                                 'reference': '123455'},
                                                                    'relation': 'increases',
                                                                    'object': {'modifier': 'Translocation', 'effect': {
                                                                        'fromLoc': {'namespace': 'GOCC',
                                                                                    'name': 'cell surface'},
                                                                        'toLoc': {'namespace': 'GOCC',
                                                                                  'name': 'endosome'}}}}),
            (('RNA', 'HGNC', 'AKT1'), ('RNA', 'HGNC', 'AKT1', ('hgvs', 'delCTT'), ('hgvs', 'p.Phe508del')),
             {'relation': 'hasVariant'}),
            (('RNA', 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week #2', 'reference': '123456'},
              'relation': 'translatedTo'}),
            (('RNA', 'HGNC', 'AKT1', ('hgvs', 'delCTT'), ('hgvs', 'p.Phe508del')),
             ('RNAFusion', ('HGNC', 'TMPRSS2'), ('r', 1, 79), ('HGNC', 'ERG'), ('r', 312, 5034)),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'directlyIncreases'}),
            (('RNAFusion', ('HGNC', 'TMPRSS2'), ('?',), ('HGNC', 'ERG'), ('?',)),
             ('Complex', ('Gene', 'HGNC', 'NCF1'), (PROTEIN, 'HGNC', 'HBP1')),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'increases'}),
            (('Complex', ('Gene', 'HGNC', 'NCF1'), (PROTEIN, 'HGNC', 'HBP1')), (PROTEIN, 'HGNC', 'HBP1'),
             {'relation': 'hasComponent'}),
            (('Complex', ('Gene', 'HGNC', 'NCF1'), (PROTEIN, 'HGNC', 'HBP1')), ('Gene', 'HGNC', 'NCF1'),
             {'relation': 'hasComponent'}),
            (('RNAFusion', ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
             ('Complex', (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')),
             {'SupportingText': 'These are mostly made up',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week', 'reference': '123455'},
              'relation': 'increases'}),
            (('Complex', (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')), (PROTEIN, 'HGNC', 'FOS'),
             {'relation': 'hasComponent'}),
            (('Complex', (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')), (PROTEIN, 'HGNC', 'JUN'),
             {'relation': 'hasComponent'}),
            (('RNA', 'HGNC', 'CFTR'), ('RNA', 'HGNC', 'CFTR', ('hgvs', 'r.1521_1523delcuu')),
             {'relation': 'hasVariant'}),
            (('RNA', 'HGNC', 'CFTR'), ('RNA', 'HGNC', 'CFTR', ('hgvs', 'r.1653_1655delcuu')),
             {'relation': 'hasVariant'}),
            (('Composite', ('Complex', 'GOCC', 'interleukin-23 complex'), (PROTEIN, 'HGNC', 'IL6')),
             (PROTEIN, 'HGNC', 'IL6'), {'relation': 'hasComponent'}),
            (('Composite', ('Complex', 'GOCC', 'interleukin-23 complex'), (PROTEIN, 'HGNC', 'IL6')),
             ('Complex', 'GOCC', 'interleukin-23 complex'), {'relation': 'hasComponent'}),
            (('Composite', ('Complex', 'GOCC', 'interleukin-23 complex'), (PROTEIN, 'HGNC', 'IL6')),
             ('BiologicalProcess', 'GOBP', 'cell cycle arrest'), {'SupportingText': 'These are mostly made up',
                                                                  'citation': {'type': 'PubMed',
                                                                               'name': 'That one article from last week',
                                                                               'reference': '123455'},
                                                                  'relation': 'decreases'}),
            (('Reaction', (('Abundance', ('CHEBI', 'superoxide')),),
              (('Abundance', ('CHEBI', 'dioxygen')), ('Abundance', ('CHEBI', 'hydrogen peroxide')))),
             ('Abundance', 'CHEBI', 'superoxide'), {'relation': 'hasReactant'}),
            (('Reaction', (('Abundance', ('CHEBI', 'superoxide')),),
              (('Abundance', ('CHEBI', 'dioxygen')), ('Abundance', ('CHEBI', 'hydrogen peroxide')))),
             ('Abundance', 'CHEBI', 'hydrogen peroxide'), {'relation': 'hasProduct'}),
            (('Reaction', (('Abundance', ('CHEBI', 'superoxide')),),
              (('Abundance', ('CHEBI', 'dioxygen')), ('Abundance', ('CHEBI', 'hydrogen peroxide')))),
             ('Abundance', 'CHEBI', 'dioxygen'), {'relation': 'hasProduct'}),
            ((PROTEIN, 'HGNC', 'CAT'), ('Abundance', 'CHEBI', 'hydrogen peroxide'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week #2', 'reference': '123456'},
              'relation': 'directlyDecreases',
              'subject': {'location': {'namespace': 'GOCC', 'name': 'intracellular'}}}),
            (('Gene', 'HGNC', 'CAT'), ('Abundance', 'CHEBI', 'hydrogen peroxide'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week #2', 'reference': '123456'},
              'relation': 'directlyDecreases',
              'subject': {'location': {'namespace': 'GOCC', 'name': 'intracellular'}}}),
            ((PROTEIN, 'HGNC', 'HMGCR'), ('BiologicalProcess', 'GOBP', 'cholesterol biosynthetic process'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week #2', 'reference': '123456'},
              'relation': 'rateLimitingStepOf',
              'subject': {'modifier': 'Activity', 'effect': {'namespace': 'PYBEL', 'name': 'cat'}}}),
            (('Gene', 'HGNC', 'APP', ('hgvs', 'g.275341G>C')), ('Pathology', 'MESHD', 'Alzheimer Disease'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week #2', 'reference': '123456'},
              'relation': 'causesNoChange'}),
            (('Gene', 'HGNC', 'APP'), ('Gene', 'HGNC', 'APP', ('hgvs', 'g.275341G>C')), {'relation': 'hasVariant'}),
            (('Complex', (PROTEIN, 'HGNC', 'F3'), (PROTEIN, 'HGNC', 'F7')), (PROTEIN, 'HGNC', 'F3'),
             {'relation': 'hasComponent'}),
            (('Complex', (PROTEIN, 'HGNC', 'F3'), (PROTEIN, 'HGNC', 'F7')), (PROTEIN, 'HGNC', 'F7'),
             {'relation': 'hasComponent'}),
            (('Complex', (PROTEIN, 'HGNC', 'F3'), (PROTEIN, 'HGNC', 'F7')), (PROTEIN, 'HGNC', 'F9'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week #2', 'reference': '123456'},
              'relation': 'regulates',
              'subject': {'modifier': 'Activity', 'effect': {'name': 'pep', 'namespace': 'PYBEL'}},
              'object': {'modifier': 'Activity', 'effect': {'name': 'pep', 'namespace': 'PYBEL'}}}),
            ((PROTEIN, 'HGNC', 'GSK3B', ('pmod', ('PYBEL', 'Ph'), 'Ser', 9)), (PROTEIN, 'HGNC', 'GSK3B'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week #2', 'reference': '123456'},
              'relation': 'positiveCorrelation',
              'object': {'modifier': 'Activity', 'effect': {'namespace': 'PYBEL', 'name': 'kin'}}}),
            ((PROTEIN, 'HGNC', 'GSK3B'), (PROTEIN, 'HGNC', 'GSK3B', ('pmod', ('PYBEL', 'Ph'), 'Ser', 9)),
             {'relation': 'hasVariant'}),
            ((PROTEIN, 'HGNC', 'GSK3B'), (PROTEIN, 'HGNC', 'GSK3B', ('pmod', ('PYBEL', 'Ph'), 'Ser', 9)),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week #2', 'reference': '123456'},
              'relation': 'positiveCorrelation',
              'subject': {'modifier': 'Activity', 'effect': {'namespace': 'PYBEL', 'name': 'kin'}}}),
            (('Pathology', 'MESHD', 'Psoriasis'), ('Pathology', 'MESHD', 'Skin Diseases'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week #2', 'reference': '123456'},
              'relation': 'isA'}),
            (('Reaction', (
                ('Abundance', ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), ('Abundance', ('CHEBI', 'NADPH')),
                ('Abundance', ('CHEBI', 'hydron'))),
              (('Abundance', ('CHEBI', 'NADP(+)')), ('Abundance', ('CHEBI', 'mevalonate')))),
             ('Abundance', 'CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'), {'relation': 'hasReactant'}),
            (('Reaction', (
                ('Abundance', ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), ('Abundance', ('CHEBI', 'NADPH')),
                ('Abundance', ('CHEBI', 'hydron'))),
              (('Abundance', ('CHEBI', 'NADP(+)')), ('Abundance', ('CHEBI', 'mevalonate')))),
             ('Abundance', 'CHEBI', 'NADPH'), {'relation': 'hasReactant'}),
            (('Reaction', (
                ('Abundance', ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), ('Abundance', ('CHEBI', 'NADPH')),
                ('Abundance', ('CHEBI', 'hydron'))),
              (('Abundance', ('CHEBI', 'NADP(+)')), ('Abundance', ('CHEBI', 'mevalonate')))),
             ('Abundance', 'CHEBI', 'hydron'), {'relation': 'hasReactant'}),
            (('Reaction', (
                ('Abundance', ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), ('Abundance', ('CHEBI', 'NADPH')),
                ('Abundance', ('CHEBI', 'hydron'))),
              (('Abundance', ('CHEBI', 'NADP(+)')), ('Abundance', ('CHEBI', 'mevalonate')))),
             ('Abundance', 'CHEBI', 'mevalonate'), {'relation': 'hasProduct'}),
            (('Reaction', (
                ('Abundance', ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), ('Abundance', ('CHEBI', 'NADPH')),
                ('Abundance', ('CHEBI', 'hydron'))),
              (('Abundance', ('CHEBI', 'NADP(+)')), ('Abundance', ('CHEBI', 'mevalonate')))),
             ('Abundance', 'CHEBI', 'NADP(+)'), {'relation': 'hasProduct'}),
            (('Reaction', (
                ('Abundance', ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), ('Abundance', ('CHEBI', 'NADPH')),
                ('Abundance', ('CHEBI', 'hydron'))),
              (('Abundance', ('CHEBI', 'NADP(+)')), ('Abundance', ('CHEBI', 'mevalonate')))),
             ('BiologicalProcess', 'GOBP', 'cholesterol biosynthetic process'),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week #2', 'reference': '123456'},
              'relation': 'subProcessOf'}),
            (('Abundance', 'CHEBI', 'nitric oxide'),
             ('Complex', (PROTEIN, 'HGNC', 'ITGAV'), (PROTEIN, 'HGNC', 'ITGB3')),
             {'SupportingText': 'These were all explicitly stated in the BEL 2.0 Specification',
              'citation': {'type': 'PubMed', 'name': 'That one article from last week #2', 'reference': '123456'},
              'relation': 'increases', 'object': {'modifier': 'Translocation',
                                                  'effect': {'fromLoc': {'namespace': 'GOCC', 'name': 'intracellular'},
                                                             'toLoc': {'namespace': 'GOCC', 'name': 'cell surface'}}}}),
            (('Complex', (PROTEIN, 'HGNC', 'ITGAV'), (PROTEIN, 'HGNC', 'ITGB3')), (PROTEIN, 'HGNC', 'ITGAV'),
             {'relation': 'hasComponent'}),
            (('Complex', (PROTEIN, 'HGNC', 'ITGAV'), (PROTEIN, 'HGNC', 'ITGB3')), (PROTEIN, 'HGNC', 'ITGB3'),
             {'relation': 'hasComponent'}),

        ]

        for u, v, d in e:
            assertHasEdge(self, u, v, g, **d)
