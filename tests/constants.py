# -*- coding: utf-8 -*-

import logging
import os
import tempfile
import unittest
from json import dumps

from requests.compat import urlparse

from pybel import BELGraph
from pybel.constants import *
from pybel.manager.cache import CacheManager
from pybel.parser.parse_bel import BelParser
from pybel.parser.parse_exceptions import *
from pybel.parser.utils import any_subdict_matches

log = logging.getLogger(__name__)

dir_path = os.path.dirname(os.path.realpath(__file__))
owl_dir_path = os.path.join(dir_path, 'owl')
bel_dir_path = os.path.join(dir_path, 'bel')
belns_dir_path = os.path.join(dir_path, 'belns')
belanno_dir_path = os.path.join(dir_path, 'belanno')
beleq_dir_path = os.path.join(dir_path, 'beleq')

test_bel_simple = os.path.join(bel_dir_path, 'test_bel.bel')
test_bel_extensions = os.path.join(bel_dir_path, 'test_bel_owl_extension.bel')
test_bel_slushy = os.path.join(bel_dir_path, 'slushy.bel')
test_bel_thorough = os.path.join(bel_dir_path, 'thorough.bel')
test_bel_isolated = os.path.join(bel_dir_path, 'isolated.bel')
test_bel_misordered = os.path.join(bel_dir_path, 'misordered.bel')

test_owl_pizza = os.path.join(owl_dir_path, 'pizza_onto.owl')
test_owl_wine = os.path.join(owl_dir_path, 'wine.owl')
test_owl_ado = os.path.join(owl_dir_path, 'ado.owl')

test_an_1 = os.path.join(belanno_dir_path, 'test_an_1.belanno')

test_ns_1 = os.path.join(belns_dir_path, 'test_ns_1.belns')
test_ns_2 = os.path.join(belns_dir_path, 'test_ns_1_updated.belns')
test_ns_nocache = os.path.join(belns_dir_path, 'test_nocache.belns')

test_eq_1 = os.path.join(beleq_dir_path, 'disease-ontology.beleq')
test_eq_2 = os.path.join(beleq_dir_path, 'mesh-diseases.beleq')

test_citation_dict = {
    CITATION_TYPE: 'PubMed',
    CITATION_NAME: 'TestName',
    CITATION_REFERENCE: '1235813'
}
SET_CITATION_TEST = 'SET Citation = {{"{type}","{name}","{reference}"}}'.format(**test_citation_dict)
test_evidence_text = 'I read it on Twitter'
test_set_evidence = 'SET Evidence = "{}"'.format(test_evidence_text)

CHEBI_KEYWORD = 'CHEBI'
CHEBI_URL = DEFAULT_NAMESPACE_RESOURCES + 'chebi.belns'
CELL_LINE_KEYWORD = 'CellLine'
CELL_LINE_URL = DEFAULT_ANNOTATION_RESOURCES + 'cell-line.belanno'
HGNC_KEYWORD = 'HGNC'
HGNC_URL = DEFAULT_NAMESPACE_RESOURCES + 'hgnc-human-genes.belns'
MESH_DISEASES_KEYWORD = 'MeSHDisease'
MESH_DISEASES_URL = DEFAULT_ANNOTATION_RESOURCES + "mesh-diseases.belanno"

pizza_iri = 'http://www.lesfleursdunormal.fr/static/_downloads/pizza_onto.owl'
wine_iri = 'http://www.w3.org/TR/2003/PR-owl-guide-20031209/wine'

AKT1 = (PROTEIN, 'HGNC', 'AKT1')
EGFR = (PROTEIN, 'HGNC', 'EGFR')
FADD = (PROTEIN, 'HGNC', 'FADD')
CASP8 = (PROTEIN, 'HGNC', 'CASP8')


def update_provenance(bel_parser):
    """Sticks provenance in a BEL parser
    
    :param pybel.parser.parse_bel.BelParser bel_parser: 
    :return: 
    """
    bel_parser.control_parser.citation.update(test_citation_dict)
    bel_parser.control_parser.evidence = test_evidence_text


def any_dict_matches(dict_of_dicts, query_dict):
    return any(query_dict == sd for sd in dict_of_dicts.values())


def assertHasNode(self, node, graph, **kwargs):
    """A helper function for checking if a node with the given properties is contained within a graph

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


def assertHasEdge(self, u, v, graph, permissive=True, **kwargs):
    """A helper function for checking if an edge with the given properties is contained within a graph

    :param self: A TestCase
    :type self: unittest.TestCase
    :param u: source node
    :type u: tuple
    :param v: target node
    :type v: tuple
    :param graph: underlying graph
    :type graph: BELGraph
    :param kwargs: splat the data to match
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


def identifier(namespace, name):
    return {NAMESPACE: namespace, NAME: name}


def default_identifier(name):
    """Convenience function for building a default namespace/name pair"""
    return identifier(BEL_DEFAULT_NAMESPACE, name)


class TestGraphMixin(unittest.TestCase):
    def assertHasNode(self, g, n, **kwargs):
        """Helper for asserting node membership
        
        :param g: Graph 
        :param n: Node
        :param kwargs: 
        """
        assertHasNode(self, n, g, **kwargs)

    def assertHasEdge(self, g, u, v, **kwargs):
        """Helper for asserting edge membership
        
        :param g: Graph
        :param u: Source node
        :param v: Target node
        :param kwargs: 
        """
        assertHasEdge(self, u, v, g, **kwargs)


class TemporaryCacheClsMixin(unittest.TestCase):
    """Facilitates generating a database in a temporary file on a class-by-class basis"""

    @classmethod
    def setUpClass(cls):
        cls.test_connection = os.environ.get('PYBEL_TEST_CONNECTION')

        if cls.test_connection:
            cls.connection = cls.test_connection
        else:
            cls.fd, cls.path = tempfile.mkstemp()
            cls.connection = 'sqlite:///' + cls.path
            log.info('Test generated connection string %s', cls.connection)

        cls.manager = CacheManager(connection=cls.connection)
        cls.manager.create_all()

    @classmethod
    def tearDownClass(cls):
        cls.manager.session.close()
        if not cls.test_connection:
            os.close(cls.fd)
            os.remove(cls.path)


class FleetingTemporaryCacheMixin(TemporaryCacheClsMixin):
    """This class makes a manager available for the entire existence of the class but deletes everything that gets
    stuck in it after each test"""

    def setUp(self):
        super(FleetingTemporaryCacheMixin, self).setUp()

        self.manager.drop_namespaces()
        self.manager.drop_annotations()
        self.manager.drop_networks()


class TestTokenParserBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = BELGraph()
        cls.parser = BelParser(cls.graph, autostreamline=False)

    def setUp(self):
        self.parser.clear()

    def assertHasNode(self, member, **kwargs):
        assertHasNode(self, member, self.parser.graph, **kwargs)

    def assertHasEdge(self, u, v, **kwargs):
        assertHasEdge(self, u, v, self.parser.graph, **kwargs)


expected_test_simple_metadata = {
    METADATA_NAME: "PyBEL Test Simple",
    METADATA_DESCRIPTION: "Made for testing PyBEL parsing",
    METADATA_VERSION: "1.6.0",
    METADATA_COPYRIGHT: "Copyright (c) Charles Tapley Hoyt. All Rights Reserved.",
    METADATA_AUTHORS: "Charles Tapley Hoyt",
    METADATA_LICENSES: "WTF License",
    METADATA_CONTACT: "charles.hoyt@scai.fraunhofer.de"
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

expected_test_bel_4_metadata = {
    METADATA_NAME: "PyBEL Test OWL Extension",
    METADATA_DESCRIPTION: "Tests the use of OWL ontologies as namespaces",
    METADATA_VERSION: "1.6.0",
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


def build_variant_dict(variant):
    """A convenience function for building a variant dictionary"""
    return {KIND: HGVS, IDENTIFIER: variant}


def get_uri_name(url):
    """Gets the file name from the end of the URL. Only useful for PyBEL's testing though since it looks specifically
    if the file is from the weird owncloud resources distributed by Fraunhofer"""
    url_parsed = urlparse(url)

    if url.startswith(FRAUNHOFER_RESOURCES):
        return url_parsed.query.split('=')[-1]
    else:
        url_parts = url_parsed.path.split('/')
        return url_parts[-1]


def help_check_hgnc(self, namespace_dict):
    self.assertIn(HGNC_KEYWORD, namespace_dict)

    self.assertIn('MHS2', namespace_dict[HGNC_KEYWORD])
    self.assertEqual(set('G'), set(namespace_dict[HGNC_KEYWORD]['MHS2']))

    self.assertIn('MIATNB', namespace_dict[HGNC_KEYWORD])
    self.assertEqual(set('GR'), set(namespace_dict[HGNC_KEYWORD]['MIATNB']))

    self.assertIn('MIA', namespace_dict[HGNC_KEYWORD])
    self.assertEqual(set('GRP'), set(namespace_dict[HGNC_KEYWORD]['MIA']))


BEL_THOROUGH_NODES = {
    (ABUNDANCE, 'CHEBI', 'oxygen atom'),
    (GENE, 'HGNC', 'AKT1', (GMOD, (BEL_DEFAULT_NAMESPACE, 'Me'))),
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
    (PROTEIN, 'HGNC', 'HRAS', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Palm'))),
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

BEL_THOROUGH_EDGES = [
    ((ABUNDANCE, 'CHEBI', 'oxygen atom'), (GENE, 'HGNC', 'AKT1', (GMOD, (BEL_DEFAULT_NAMESPACE, 'Me'))), {
        EVIDENCE: 'These are mostly made up',
        CITATION: citation_1,
        RELATION: INCREASES,
        ANNOTATIONS: {
            'TESTAN1': '1',
            'TestRegex': '9000'
        }
    }),
    ((ABUNDANCE, 'CHEBI', 'oxygen atom'), (GENE, 'HGNC', 'AKT1', (GMOD, (BEL_DEFAULT_NAMESPACE, 'Me'))), {
        EVIDENCE: 'These are mostly made up',
        CITATION: citation_1,
        RELATION: INCREASES,
        ANNOTATIONS: {
            'TESTAN1': '2',
            'TestRegex': '9000'
        }
    }),
    ((GENE, 'HGNC', 'AKT1'), (GENE, 'HGNC', 'AKT1', (GMOD, (BEL_DEFAULT_NAMESPACE, 'Me'))), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((GENE, 'HGNC', 'AKT1'), (ABUNDANCE, 'CHEBI', 'oxygen atom'), {
        EVIDENCE: 'These are mostly made up',
        CITATION: citation_1,
        RELATION: DECREASES, SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
        OBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
        ANNOTATIONS: {}
    }),
    ((GENE, 'HGNC', 'AKT1'), (GENE, 'HGNC', 'AKT1', (HGVS, 'p.Phe508del')), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((GENE, 'HGNC', 'AKT1'), (GENE, 'HGNC', 'AKT1', (HGVS, 'c.308G>A')), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((GENE, 'HGNC', 'AKT1'),
     (GENE, 'HGNC', 'AKT1', (HGVS, 'c.1521_1523delCTT'), (HGVS, 'c.308G>A'), (HGVS, 'p.Phe508del')), {
         RELATION: HAS_VARIANT,
         ANNOTATIONS: {}
     }),
    ((GENE, 'HGNC', 'AKT1'), (RNA, 'HGNC', 'AKT1'), {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: TRANSCRIBED_TO,
        ANNOTATIONS: {}
    }),
    ((GENE, 'HGNC', 'AKT1', (HGVS, 'p.Phe508del')), (PROTEIN, 'HGNC', 'AKT1'), {
        EVIDENCE: 'These are mostly made up',
        CITATION: citation_1,
        RELATION: DIRECTLY_DECREASES,
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 473)), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.C40*')), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'AKT1'),
     (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Ala127Tyr'), (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser')), {
         RELATION: HAS_VARIANT,
         ANNOTATIONS: {}
     }),
    ((PROTEIN, 'HGNC', 'AKT1'),
     (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Ala127Tyr'), (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser')), {
         EVIDENCE: 'These are mostly made up',
         CITATION: citation_1,
         RELATION: DIRECTLY_DECREASES,
         SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
         OBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
         ANNOTATIONS: {}
     }),
    ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Arg1851*')), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.40*')), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, '?')), {
        EVIDENCE: 'These are mostly made up',
        CITATION: citation_1,
        RELATION: INCREASES,
        SUBJECT: {MODIFIER: DEGRADATION},
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'CFTR', (HGVS, 'p.Gly576Ala')), {
        EVIDENCE: 'These are mostly made up',
        CITATION: citation_1,
        RELATION: INCREASES,
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'AKT1'), (RNA, 'HGNC', 'CFTR', (HGVS, 'r.1521_1523delcuu')), {
        EVIDENCE: 'These are mostly made up',
        CITATION: citation_1,
        RELATION: INCREASES,
        SUBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'kin'}},
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'AKT1'), (RNA, 'HGNC', 'CFTR', (HGVS, 'r.1653_1655delcuu')), {
        EVIDENCE: 'These are mostly made up',
        CITATION: citation_1,
        RELATION: INCREASES,
        SUBJECT: {MODIFIER: ACTIVITY},
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'EGFR'), {
        EVIDENCE: 'These are mostly made up',
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
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'EGFR'), {
        EVIDENCE: 'These are mostly made up',
        CITATION: citation_1,
        RELATION: INCREASES,
        SUBJECT: {
            MODIFIER: ACTIVITY,
            EFFECT: {NAME: 'kin', NAMESPACE: BEL_DEFAULT_NAMESPACE}
        },
        OBJECT: {
            MODIFIER: TRANSLOCATION,
            EFFECT: {
                FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'intracellular'},
                TO_LOC: {NAMESPACE: 'GOCC', NAME: 'extracellular space'}
            }
        },
        ANNOTATIONS: {}
    }),
    ((GENE, 'HGNC', 'AKT1', (HGVS, 'c.308G>A')),
     (GENE, ('HGNC', 'TMPRSS2'), ('c', 1, 79), ('HGNC', 'ERG'), ('c', 312, 5034)), {
         EVIDENCE: 'These are mostly made up',
         CITATION: citation_1,
         RELATION: CAUSES_NO_CHANGE,
         ANNOTATIONS: {}
     }),
    ((GENE, 'HGNC', 'AKT1', (HGVS, 'c.308G>A')),
     (GENE, 'HGNC', 'AKT1', (HGVS, 'c.1521_1523delCTT'), (HGVS, 'c.308G>A'), (HGVS, 'p.Phe508del')), {
         EVIDENCE: 'These are mostly made up',
         CITATION: citation_1,
         RELATION: INCREASES,
         SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
         ANNOTATIONS: {}
     }),
    ((MIRNA, 'HGNC', 'MIR21'),
     (GENE, ('HGNC', 'BCR'), ('c', '?', 1875), ('HGNC', 'JAK2'), ('c', 2626, '?')),
     {
         EVIDENCE: 'These are mostly made up',
         CITATION: citation_1,
         RELATION: DIRECTLY_INCREASES,
         ANNOTATIONS: {}
     }),
    ((MIRNA, 'HGNC', 'MIR21'), (PROTEIN, 'HGNC', 'AKT1', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 473)),
     {
         EVIDENCE: 'These are mostly made up',
         CITATION: citation_1,
         RELATION: DECREASES,
         SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
         ANNOTATIONS: {}
     }),
    ((MIRNA, 'HGNC', 'MIR21'), (MIRNA, 'HGNC', 'MIR21', (HGVS, 'p.Phe508del')), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')), (PROTEIN, 'HGNC', 'AKT1'),
     {
         EVIDENCE: 'These are mostly made up',
         CITATION: citation_1,
         RELATION: INCREASES,
         OBJECT: {MODIFIER: DEGRADATION},
         ANNOTATIONS: {}
     }),
    ((GENE, 'HGNC', 'CFTR'), (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((GENE, 'HGNC', 'CFTR'), (GENE, 'HGNC', 'CFTR', (HGVS, 'g.117199646_117199648delCTT')), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((GENE, 'HGNC', 'CFTR'), (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((GENE, 'HGNC', 'CFTR', (HGVS, 'g.117199646_117199648delCTT')),
     (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')), {
         EVIDENCE: 'These are mostly made up',
         CITATION: citation_1,
         RELATION: INCREASES, ANNOTATIONS: {}
     }),
    ((MIRNA, 'HGNC', 'MIR21', (HGVS, 'p.Phe508del')), (PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.C40*')),
     {
         EVIDENCE: 'These are mostly made up',
         CITATION: citation_1,
         RELATION: INCREASES,
         SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
         ANNOTATIONS: {}
     }),
    ((GENE, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
     (PROTEIN, ('HGNC', 'TMPRSS2'), ('p', 1, 79), ('HGNC', 'ERG'), ('p', 312, 5034)), {
         EVIDENCE: 'These are mostly made up',
         CITATION: citation_1,
         RELATION: INCREASES, ANNOTATIONS: {}
     }),
    ((PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.Arg1851*')),
     (PROTEIN, ('HGNC', 'BCR'), ('p', '?', 1875), ('HGNC', 'JAK2'), ('p', 2626, '?')), {
         EVIDENCE: 'These are mostly made up',
         CITATION: citation_1,
         RELATION: INCREASES, ANNOTATIONS: {}
     }),
    ((PROTEIN, 'HGNC', 'AKT1', (HGVS, 'p.40*')),
     (PROTEIN, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
     {
         EVIDENCE: 'These are mostly made up',
         CITATION: citation_1,
         RELATION: INCREASES, ANNOTATIONS: {}
     }),
    ((PROTEIN, 'HGNC', 'CFTR', (HGVS, '=')), (PROTEIN, 'HGNC', 'EGFR'), {
        EVIDENCE: 'These are mostly made up',
        CITATION: citation_1,
        RELATION: INCREASES,
        OBJECT: {
            MODIFIER: TRANSLOCATION,
            EFFECT: {
                FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'intracellular'},
                TO_LOC: {NAMESPACE: 'GOCC', NAME: 'cell surface'}
            }
        },
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'CFTR'), (PROTEIN, 'HGNC', 'CFTR', (HGVS, '=')), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'CFTR'), (PROTEIN, 'HGNC', 'CFTR', (HGVS, '?')), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'CFTR'), (PROTEIN, 'HGNC', 'CFTR', (HGVS, 'p.Phe508del')), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'CFTR'), (PROTEIN, 'HGNC', 'CFTR', (HGVS, 'p.Gly576Ala')), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'CFTR', (HGVS, '?')), (PATHOLOGY, 'MESHD', 'Adenocarcinoma'),
     {
         EVIDENCE: 'These are mostly made up',
         CITATION: citation_1,
         RELATION: INCREASES, ANNOTATIONS: {}
     }),
    ((PROTEIN, 'HGNC', 'MIA', (FRAGMENT, (5, 20))), (COMPLEX, 'GOCC', 'interleukin-23 complex'), {
        EVIDENCE: 'These are mostly made up',
        CITATION: citation_1,
        RELATION: INCREASES,
        OBJECT: {
            MODIFIER: TRANSLOCATION,
            EFFECT: {
                FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'intracellular'},
                TO_LOC: {NAMESPACE: 'GOCC', NAME: 'extracellular space'}
            }
        },
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'MIA'), (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, (5, 20))), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'MIA'), (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, (1, '?'))), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'MIA'), (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, '?')), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'MIA'), (PROTEIN, 'HGNC', 'MIA', (FRAGMENT, '?', '55kD')), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'MIA', (FRAGMENT, (1, '?'))), (PROTEIN, 'HGNC', 'EGFR'), {
        EVIDENCE: 'These are mostly made up',
        CITATION: citation_1,
        RELATION: INCREASES,
        OBJECT: {
            MODIFIER: TRANSLOCATION,
            EFFECT: {
                FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'cell surface'},
                TO_LOC: {NAMESPACE: 'GOCC', NAME: 'endosome'}}
        },
        ANNOTATIONS: {}
    }),
    ((RNA, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'EGFR'), {
        EVIDENCE: 'These are mostly made up',
        CITATION: citation_1,
        RELATION: INCREASES,
        OBJECT: {MODIFIER: TRANSLOCATION, EFFECT: {
            FROM_LOC: {NAMESPACE: 'GOCC', NAME: 'cell surface'},
            TO_LOC: {NAMESPACE: 'GOCC', NAME: 'endosome'}}},
        ANNOTATIONS: {}
    }),
    ((RNA, 'HGNC', 'AKT1'), (RNA, 'HGNC', 'AKT1', (HGVS, 'c.1521_1523delCTT'), (HGVS, 'p.Phe508del')), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((RNA, 'HGNC', 'AKT1'), (PROTEIN, 'HGNC', 'AKT1'), {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: TRANSLATED_TO,
        ANNOTATIONS: {}
    }),
    ((RNA, 'HGNC', 'AKT1', (HGVS, 'c.1521_1523delCTT'), (HGVS, 'p.Phe508del')),
     (RNA, ('HGNC', 'TMPRSS2'), ('r', 1, 79), ('HGNC', 'ERG'), ('r', 312, 5034)), {
         EVIDENCE: 'These are mostly made up',
         CITATION: citation_1,
         RELATION: DIRECTLY_INCREASES,
         ANNOTATIONS: {}
     }),
    ((RNA, ('HGNC', 'TMPRSS2'), ('?',), ('HGNC', 'ERG'), ('?',)),
     (COMPLEX, (GENE, 'HGNC', 'NCF1'), (PROTEIN, 'HGNC', 'HBP1')), {
         EVIDENCE: 'These are mostly made up',
         CITATION: citation_1,
         RELATION: INCREASES,
         ANNOTATIONS: {}
     }),
    ((COMPLEX, (GENE, 'HGNC', 'NCF1'), (PROTEIN, 'HGNC', 'HBP1')), (PROTEIN, 'HGNC', 'HBP1'), {
        RELATION: HAS_COMPONENT,
        ANNOTATIONS: {}
    }),
    ((COMPLEX, (GENE, 'HGNC', 'NCF1'), (PROTEIN, 'HGNC', 'HBP1')), (GENE, 'HGNC', 'NCF1'), {
        RELATION: HAS_COMPONENT,
        ANNOTATIONS: {}
    }),
    ((RNA, ('HGNC', 'CHCHD4'), ('?',), ('HGNC', 'AIFM1'), ('?',)),
     (COMPLEX, (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')),
     {
         EVIDENCE: 'These are mostly made up',
         CITATION: citation_1,
         RELATION: INCREASES,
         ANNOTATIONS: {}
     }),
    ((COMPLEX, (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')), (PROTEIN, 'HGNC', 'FOS'), {
        RELATION: HAS_COMPONENT,
        ANNOTATIONS: {}
    }),
    ((COMPLEX, (PROTEIN, 'HGNC', 'FOS'), (PROTEIN, 'HGNC', 'JUN')), (PROTEIN, 'HGNC', 'JUN'), {
        RELATION: HAS_COMPONENT,
        ANNOTATIONS: {}
    }),
    ((RNA, 'HGNC', 'CFTR'), (RNA, 'HGNC', 'CFTR', (HGVS, 'r.1521_1523delcuu')), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((RNA, 'HGNC', 'CFTR'), (RNA, 'HGNC', 'CFTR', (HGVS, 'r.1653_1655delcuu')), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((COMPOSITE, (COMPLEX, 'GOCC', 'interleukin-23 complex'), (PROTEIN, 'HGNC', 'IL6')),
     (PROTEIN, 'HGNC', 'IL6'), {
         RELATION: HAS_COMPONENT,
         ANNOTATIONS: {}
     }),
    ((COMPOSITE, (COMPLEX, 'GOCC', 'interleukin-23 complex'), (PROTEIN, 'HGNC', 'IL6')),
     (COMPLEX, 'GOCC', 'interleukin-23 complex'), {
         RELATION: HAS_COMPONENT,
         ANNOTATIONS: {}
     }),
    ((COMPOSITE, (COMPLEX, 'GOCC', 'interleukin-23 complex'), (PROTEIN, 'HGNC', 'IL6')),
     (BIOPROCESS, 'GOBP', 'cell cycle arrest'), {
         EVIDENCE: 'These are mostly made up',
         CITATION: citation_1,
         RELATION: DECREASES,
         ANNOTATIONS: {}
     }),
    ((PROTEIN, 'HGNC', 'CAT'), (ABUNDANCE, 'CHEBI', 'hydrogen peroxide'),
     {
         EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
         CITATION: citation_2,
         RELATION: DIRECTLY_DECREASES,
         SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
         ANNOTATIONS: {}
     }),
    ((GENE, 'HGNC', 'CAT'), (ABUNDANCE, 'CHEBI', 'hydrogen peroxide'), {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: DIRECTLY_DECREASES,
        SUBJECT: {LOCATION: {NAMESPACE: 'GOCC', NAME: 'intracellular'}},
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'HMGCR'), (BIOPROCESS, 'GOBP', 'cholesterol biosynthetic process'), {
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
        CITATION: citation_2,
        RELATION: RATE_LIMITING_STEP_OF,
        SUBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'cat'}},
        ANNOTATIONS: {}
    }),
    ((GENE, 'HGNC', 'APP', (HGVS, 'c.275341G>C')), (PATHOLOGY, 'MESHD', 'Alzheimer Disease'),
     {
         EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
         CITATION: citation_2,
         RELATION: CAUSES_NO_CHANGE,
         ANNOTATIONS: {}
     }),
    ((GENE, 'HGNC', 'APP'), (GENE, 'HGNC', 'APP', (HGVS, 'c.275341G>C')), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((COMPLEX, (PROTEIN, 'HGNC', 'F3'), (PROTEIN, 'HGNC', 'F7')), (PROTEIN, 'HGNC', 'F3'), {
        RELATION: HAS_COMPONENT,
        ANNOTATIONS: {}
    }),
    ((COMPLEX, (PROTEIN, 'HGNC', 'F3'), (PROTEIN, 'HGNC', 'F7')), (PROTEIN, 'HGNC', 'F7'), {
        RELATION: HAS_COMPONENT,
        ANNOTATIONS: {}
    }),
    ((COMPLEX, (PROTEIN, 'HGNC', 'F3'), (PROTEIN, 'HGNC', 'F7')), (PROTEIN, 'HGNC', 'F9'),
     {
         EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
         CITATION: citation_2,
         RELATION: REGULATES,
         SUBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAME: 'pep', NAMESPACE: BEL_DEFAULT_NAMESPACE}},
         OBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAME: 'pep', NAMESPACE: BEL_DEFAULT_NAMESPACE}},
         ANNOTATIONS: {}
     }),
    ((PROTEIN, 'HGNC', 'GSK3B', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 9)), (PROTEIN, 'HGNC', 'GSK3B'),
     {
         EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
         CITATION: citation_2,
         RELATION: POSITIVE_CORRELATION,
         OBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'kin'}},
         ANNOTATIONS: {}
     }),
    ((PROTEIN, 'HGNC', 'GSK3B'), (PROTEIN, 'HGNC', 'GSK3B', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 9)), {
        RELATION: HAS_VARIANT,
        ANNOTATIONS: {}
    }),
    ((PROTEIN, 'HGNC', 'GSK3B'), (PROTEIN, 'HGNC', 'GSK3B', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Ser', 9)),
     {
         EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
         CITATION: citation_2,
         RELATION: POSITIVE_CORRELATION,
         SUBJECT: {MODIFIER: ACTIVITY, EFFECT: {NAMESPACE: BEL_DEFAULT_NAMESPACE, NAME: 'kin'}},
         ANNOTATIONS: {}
     }),
    ((PATHOLOGY, 'MESHD', 'Psoriasis'), (PATHOLOGY, 'MESHD', 'Skin Diseases'),
     {
         EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
         CITATION: citation_2,
         RELATION: IS_A,
         ANNOTATIONS: {}
     }),
    ((REACTION, (
        (ABUNDANCE, ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), (ABUNDANCE, ('CHEBI', 'NADPH')),
        (ABUNDANCE, ('CHEBI', 'hydron'))),
      ((ABUNDANCE, ('CHEBI', 'NADP(+)')), (ABUNDANCE, ('CHEBI', 'mevalonate')))),
     (ABUNDANCE, 'CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA'), {
         RELATION: HAS_REACTANT,
         ANNOTATIONS: {}
     }),
    ((REACTION, (
        (ABUNDANCE, ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), (ABUNDANCE, ('CHEBI', 'NADPH')),
        (ABUNDANCE, ('CHEBI', 'hydron'))),
      ((ABUNDANCE, ('CHEBI', 'NADP(+)')), (ABUNDANCE, ('CHEBI', 'mevalonate')))),
     (ABUNDANCE, 'CHEBI', 'NADPH'), {
         RELATION: HAS_REACTANT,
         ANNOTATIONS: {}
     }),
    ((REACTION, (
        (ABUNDANCE, ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), (ABUNDANCE, ('CHEBI', 'NADPH')),
        (ABUNDANCE, ('CHEBI', 'hydron'))),
      ((ABUNDANCE, ('CHEBI', 'NADP(+)')), (ABUNDANCE, ('CHEBI', 'mevalonate')))),
     (ABUNDANCE, 'CHEBI', 'hydron'), {
         RELATION: HAS_REACTANT,
         ANNOTATIONS: {}
     }),
    ((REACTION, (
        (ABUNDANCE, ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), (ABUNDANCE, ('CHEBI', 'NADPH')),
        (ABUNDANCE, ('CHEBI', 'hydron'))),
      ((ABUNDANCE, ('CHEBI', 'NADP(+)')), (ABUNDANCE, ('CHEBI', 'mevalonate')))),
     (ABUNDANCE, 'CHEBI', 'mevalonate'), {
         RELATION: HAS_PRODUCT,
         ANNOTATIONS: {}
     }),
    ((REACTION, (
        (ABUNDANCE, ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), (ABUNDANCE, ('CHEBI', 'NADPH')),
        (ABUNDANCE, ('CHEBI', 'hydron'))),
      ((ABUNDANCE, ('CHEBI', 'NADP(+)')), (ABUNDANCE, ('CHEBI', 'mevalonate')))),
     (ABUNDANCE, 'CHEBI', 'NADP(+)'), {
         RELATION: HAS_PRODUCT,
         ANNOTATIONS: {}
     }),
    ((REACTION, (
        (ABUNDANCE, ('CHEBI', '(3S)-3-hydroxy-3-methylglutaryl-CoA')), (ABUNDANCE, ('CHEBI', 'NADPH')),
        (ABUNDANCE, ('CHEBI', 'hydron'))),
      ((ABUNDANCE, ('CHEBI', 'NADP(+)')), (ABUNDANCE, ('CHEBI', 'mevalonate')))),
     (BIOPROCESS, 'GOBP', 'cholesterol biosynthetic process'),
     {
         EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification',
         CITATION: citation_2,
         RELATION: SUBPROCESS_OF,
         ANNOTATIONS: {}
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
         ANNOTATIONS: {}
     }),
    ((COMPLEX, (PROTEIN, 'HGNC', 'ITGAV'), (PROTEIN, 'HGNC', 'ITGB3')), (PROTEIN, 'HGNC', 'ITGAV'), {
        RELATION: HAS_COMPONENT,
        ANNOTATIONS: {}
    }),
    ((COMPLEX, (PROTEIN, 'HGNC', 'ITGAV'), (PROTEIN, 'HGNC', 'ITGB3')), (PROTEIN, 'HGNC', 'ITGB3'), {
        RELATION: HAS_COMPONENT,
        ANNOTATIONS: {}
    }),
    ((GENE, 'HGNC', 'ARRDC2'), (GENE, 'HGNC', 'ARRDC3'), {
        RELATION: EQUIVALENT_TO,
        ANNOTATIONS: {},
        CITATION: citation_2,
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification'
    }),
    ((GENE, 'HGNC', 'ARRDC3'), (GENE, 'HGNC', 'ARRDC2'), {
        RELATION: EQUIVALENT_TO,
        ANNOTATIONS: {},
        CITATION: citation_2,
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification'
    }),
    ((GENE, 'dbSNP', 'rs123456'), (GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')), {
        RELATION: ASSOCIATION,
        ANNOTATIONS: {},
        CITATION: citation_2,
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification'
    }),
    ((GENE, 'HGNC', 'CFTR', (HGVS, 'c.1521_1523delCTT')), (GENE, 'dbSNP', 'rs123456'), {
        RELATION: ASSOCIATION,
        ANNOTATIONS: {},
        CITATION: citation_2,
        EVIDENCE: 'These were all explicitly stated in the BEL 2.0 Specification'
    }),
]


class BelReconstitutionMixin(TestGraphMixin):
    def bel_simple_reconstituted(self, graph, check_metadata=True):
        """Checks that test_bel.bel was loaded properly

        :param BELGraph graph: A BEL grpah
        :param bool check_metadata: Check the graph's document section is correct
        """
        self.assertIsNotNone(graph)
        self.assertIsInstance(graph, BELGraph)
        self.assertFalse(graph.has_singleton_terms)

        if check_metadata:
            self.assertEqual(expected_test_simple_metadata, graph.document)
            self.assertEqual(expected_test_simple_metadata[METADATA_NAME], graph.name)
            self.assertEqual(expected_test_simple_metadata[METADATA_VERSION], graph.version)

        self.assertEqual(4, graph.number_of_nodes())

        # FIXME this should work, but is getting 8 for the upgrade function
        # self.assertEqual(6, graph.number_of_edges(), msg='Edges:\n{}'.format('\n'.join(map(str, graph.edges(keys=True, data=True)))))

        assertHasNode(self, AKT1, graph, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'AKT1'})
        assertHasNode(self, EGFR, graph, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'EGFR'})
        assertHasNode(self, FADD, graph, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'FADD'})
        assertHasNode(self, CASP8, graph, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'CASP8'})

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

        evidence_1 = "Evidence 1 w extra notes"
        evidence_2 = 'Evidence 2'
        evidence_3 = 'Evidence 3'

        assertHasEdge(self, AKT1, EGFR, graph, **{
            RELATION: INCREASES,
            CITATION: bel_simple_citation_1,
            EVIDENCE: evidence_1,
            ANNOTATIONS: {'Species': "9606"}
        })
        assertHasEdge(self, EGFR, FADD, graph, **{
            RELATION: DECREASES,
            ANNOTATIONS: {
                'Species': "9606",
                'CellLine': "10B9 cell"
            },
            CITATION: bel_simple_citation_1,
            EVIDENCE: evidence_2
        })
        assertHasEdge(self, EGFR, CASP8, graph, **{
            RELATION: DIRECTLY_DECREASES,
            ANNOTATIONS: {
                'Species': "9606",
                'CellLine': "10B9 cell"
            },
            CITATION: bel_simple_citation_1,
            EVIDENCE: evidence_2,
        })
        assertHasEdge(self, FADD, CASP8, graph, **{
            RELATION: INCREASES,
            ANNOTATIONS: {
                'Species': "10116"
            },
            CITATION: bel_simple_citation_2,
            EVIDENCE: evidence_3,
        })
        assertHasEdge(self, AKT1, CASP8, graph, **{
            RELATION: ASSOCIATION,
            ANNOTATIONS: {
                'Species': "10116"
            },
            CITATION: bel_simple_citation_2,
            EVIDENCE: evidence_3,
        })
        assertHasEdge(self, CASP8, AKT1, graph, **{
            RELATION: ASSOCIATION,
            ANNOTATIONS: {
                'Species': "10116"
            },
            CITATION: bel_simple_citation_2,
            EVIDENCE: evidence_3,
        })

    def bel_thorough_reconstituted(self, graph, check_metadata=True, check_warnings=True, check_provenance=True):
        """Checks that thorough.bel was loaded properly

        :param BELGraph graph: A BEL graph
        :param bool check_metadata: Check the graph's document section is correct
        :param bool check_warnings: Check the graph produced the expected warnings
        :param bool check_provenance: Check the graph's definition section is correct
        """
        self.assertIsNotNone(graph)
        self.assertIsInstance(graph, BELGraph)
        self.assertFalse(graph.has_singleton_terms)

        if check_warnings:
            self.assertEqual(0, len(graph.warnings),
                             msg='Document warnings:\n{}'.format('\n'.join(map(str, graph.warnings))))

        if check_metadata:
            self.assertLessEqual(set(expected_test_thorough_metadata), set(graph.document))
            gmd = {k: v for k, v in graph.document.items() if k in expected_test_thorough_metadata}
            self.assertEqual(expected_test_thorough_metadata, gmd)
            self.assertEqual(expected_test_thorough_metadata[METADATA_NAME], graph.name)
            self.assertEqual(expected_test_thorough_metadata[METADATA_VERSION], graph.version)
            self.assertEqual(expected_test_thorough_metadata[METADATA_DESCRIPTION], graph.description)

        if check_provenance:
            self.assertEqual({'CHEBI', 'HGNC', 'GOBP', 'GOCC', 'MESHD', 'TESTNS2'}, set(graph.namespace_url))
            self.assertEqual(set(), set(graph.namespace_owl))
            self.assertEqual({'dbSNP'}, set(graph.namespace_pattern))
            self.assertEqual(set(), set(graph.annotation_owl))
            self.assertEqual({'TESTAN1', 'TESTAN2'}, set(graph.annotation_list))
            self.assertEqual({'TestRegex'}, set(graph.annotation_pattern))

        self.assertEqual(set(BEL_THOROUGH_NODES), set(graph.nodes_iter()))

        # FIXME
        # self.assertEqual(set((u, v) for u, v, _ in e), set(g.edges()))

        for u, v, d in BEL_THOROUGH_EDGES:
            assertHasEdge(self, u, v, graph, permissive=True, **d)

    def bel_slushy_reconstituted(self, graph, check_metadata=True, check_warnings=True):
        """Check that slushy.bel was loaded properly
        
        :param BELGraph graph: A BEL graph
        :param bool check_metadata: Check the graph's document section is correct
        :param bool check_warnings: Check the graph produced the expected warnings
        """
        self.assertIsNotNone(graph)
        self.assertIsInstance(graph, BELGraph)

        if check_metadata:
            self.assertEqual(expected_test_slushy_metadata, graph.document)
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
                (98, Exception),
            ]

            for (el, ew), (l, _, w, _) in zip(expected_warnings, graph.warnings):
                self.assertEqual(el, l, msg="Expected different error on line {}. Check line {}".format(el, l))
                self.assertIsInstance(w, ew, msg='Line: {}'.format(el))

        assertHasNode(self, AKT1, graph, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'AKT1'})
        assertHasNode(self, EGFR, graph, **{FUNCTION: PROTEIN, NAMESPACE: 'HGNC', NAME: 'EGFR'})

        assertHasEdge(self, AKT1, EGFR, graph, **{
            RELATION: INCREASES,
            CITATION: citation_1,
            EVIDENCE: evidence_1,
        })

    def bel_isolated_reconstituted(self, graph):
        """Runs the isolated node test

        :param BELGraph graph: A BEL Graph
        """
        self.assertIsNotNone(graph)
        self.assertIsInstance(graph, BELGraph)
        self.assertTrue(graph.has_singleton_terms)

        a = PATHOLOGY, 'MESHD', 'Achlorhydria'
        b = PROTEIN, 'HGNC', 'ADGRB1'
        c = PROTEIN, 'HGNC', 'ADGRB2'
        d = COMPLEX, b, c

        assertHasNode(self, a, graph)
        assertHasNode(self, b, graph)
        assertHasNode(self, c, graph)
        assertHasNode(self, d, graph)

        assertHasEdge(self, d, b, graph)
        assertHasEdge(self, d, c, graph)
