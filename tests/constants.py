import os
import unittest

from pybel import BELGraph
from pybel.parser.parse_bel import BelParser
from pybel.parser.utils import any_subdict_matches

dir_path = os.path.dirname(os.path.realpath(__file__))
owl_dir_path = os.path.join(dir_path, 'owl')
bel_dir_path = os.path.join(dir_path, 'bel')
belns_dir_path = os.path.join(dir_path, 'bel')
belanno_dir_path = os.path.join(dir_path, 'bel')

test_bel_0 = os.path.join(bel_dir_path, 'small_corpus.bel')
test_bel_1 = os.path.join(bel_dir_path, 'test_bel_1.bel')
test_bel_3 = os.path.join(bel_dir_path, 'test_bel_3.bel')
test_bel_4 = os.path.join(bel_dir_path, 'test_bel_4.bel')
test_bel_slushy = os.path.join(bel_dir_path, 'slushy.bel')

test_owl_1 = os.path.join(owl_dir_path, 'pizza_onto.owl')
test_owl_2 = os.path.join(owl_dir_path, 'wine.owl')
test_owl_3 = os.path.join(owl_dir_path, 'ado.owl')

test_an_1 = os.path.join(belanno_dir_path, 'test_an_1.belanno')

test_ns_1 = os.path.join(belns_dir_path, 'test_ns_1.belns')
test_ns_2 = os.path.join(belns_dir_path, 'test_ns_1_updated.belns')

test_citation_bel = 'SET Citation = {"TestType","TestName","TestRef"}'
test_citation_dict = dict(type='TestType', name='TestName', reference='TestRef')
test_evidence_bel = 'SET Evidence = "I read it on Twitter"'
test_evidence_text = 'I read it on Twitter'

pizza_iri = "http://www.lesfleursdunormal.fr/static/_downloads/pizza_onto.owl"
wine_iri = "http://www.w3.org/TR/2003/PR-owl-guide-20031209/wine"

AKT1 = ('Protein', 'HGNC', 'AKT1')
EGFR = ('Protein', 'HGNC', 'EGFR')
FADD = ('Protein', 'HGNC', 'FADD')
CASP8 = ('Protein', 'HGNC', 'CASP8')


def assertHasNode(self, member, graph, **kwargs):
    self.assertTrue(graph.has_node(member), msg='{} not found in {}'.format(member, graph))
    if kwargs:
        self.assertTrue(all(kwarg in graph.node[member] for kwarg in kwargs),
                        msg="Missing kwarg in node data")
        self.assertEqual(kwargs, {k: graph.node[member][k] for k in kwargs},
                         msg="Wrong values in node data")


def assertHasEdge(self, u, v, graph, **kwargs):
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


class BelReconstitutionMixin(unittest.TestCase):
    def bel_1_reconstituted(self, g):
        self.assertIsNotNone(g)
        self.assertIsInstance(g, BELGraph)

        assertHasNode(self, AKT1, g, type='Protein', namespace='HGNC', name='AKT1')
        assertHasNode(self, EGFR, g, type='Protein', namespace='HGNC', name='EGFR')
        assertHasNode(self, FADD, g, type='Protein', namespace='HGNC', name='FADD')
        assertHasNode(self, CASP8, g, type='Protein', namespace='HGNC', name='CASP8')

        assertHasEdge(self, AKT1, EGFR, g, relation='increases', TESTAN1="1")
        assertHasEdge(self, EGFR, FADD, g, relation='decreases', TESTAN1="1", TESTAN2="3")
        assertHasEdge(self, EGFR, CASP8, g, relation='directlyDecreases', TESTAN1="1", TESTAN2="3")
        assertHasEdge(self, FADD, CASP8, g, relation='increases', TESTAN1="2")
        assertHasEdge(self, AKT1, CASP8, g, relation='association', TESTAN1="2")


expected_test_bel_1_metadata = {
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
