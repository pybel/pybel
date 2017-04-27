# -*- coding: utf-8 -*-

import logging
import unittest
from collections import Counter

import pybel
import sqlalchemy.exc
from pybel import from_path
from pybel.constants import *
from pybel.manager import models
from tests import constants
from tests.constants import test_bel_thorough, mock_bel_resources, \
    expected_test_thorough_metadata, test_bel_simple, expected_test_simple_metadata, TemporaryCacheMixin, \
    BelReconstitutionMixin

try:
    import cPickle as pickle
except ImportError:
    import pickle

log = logging.getLogger(__name__)


class TestGraphCache(TemporaryCacheMixin, BelReconstitutionMixin):
    def setUp(self):
        super(TestGraphCache, self).setUp()
        self.graph = from_path(test_bel_thorough, manager=self.manager, allow_nested=True)

    @mock_bel_resources
    def test_load_reload(self, mock_get):
        name = expected_test_thorough_metadata[METADATA_NAME]
        version = expected_test_thorough_metadata[METADATA_VERSION]
        description = expected_test_thorough_metadata[METADATA_DESCRIPTION]

        self.manager.insert_graph(self.graph)

        x = self.manager.list_graphs()

        self.assertEqual(1, len(x))
        self.assertEqual((1, name, version, description), x[0])

        g2 = self.manager.get_graph(name, version)
        self.bel_thorough_reconstituted(g2)

    @mock_bel_resources
    def test_integrity_failure(self, mock_get):
        """Tests that a graph with the same name and version can't be added twice"""
        self.manager.insert_graph(self.graph)

        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.manager.insert_graph(self.graph)

    @mock_bel_resources
    def test_get_versions(self, mock_get):
        TEST_V1 = '0.9'
        TEST_V2 = expected_test_thorough_metadata[METADATA_VERSION]  # Actually is 1.0

        self.graph.document[METADATA_VERSION] = TEST_V1
        self.manager.insert_graph(self.graph)

        self.graph.document[METADATA_VERSION] = TEST_V2
        self.manager.insert_graph(self.graph)

        self.assertEqual({TEST_V1, TEST_V2}, set(self.manager.get_graph_versions(self.graph.document[METADATA_NAME])))

        self.assertEqual(TEST_V2, self.manager.get_graph(self.graph.document[METADATA_NAME]).document[METADATA_VERSION])


class TestGraphCacheSimple(TemporaryCacheMixin, BelReconstitutionMixin):
    def setUp(self):
        super(TestGraphCacheSimple, self).setUp()
        self.simple_graph = pybel.from_path(test_bel_simple, manager=self.manager)
        self.manager.ensure_namespace(GOCC_LATEST)

    @mock_bel_resources
    def test_get_or_create_node(self, mock_get):
        network = self.manager.insert_graph(self.simple_graph, store_parts=True)

        citations = self.manager.session.query(models.Citation).all()
        self.assertEqual(2, len(citations))

        citations_strs = {'123455', '123456'}
        self.assertEqual(citations_strs, {e.reference for e in citations})

        authors = {'Example Author', 'Example Author2'}
        self.assertEqual(authors, {a.name for a in self.manager.session.query(models.Author).all()})

        evidences = self.manager.session.query(models.Evidence).all()
        self.assertEqual(3, len(evidences))

        evidences_strs = {'Evidence 1 w extra notes', 'Evidence 2', 'Evidence 3'}
        self.assertEqual(evidences_strs, {e.text for e in evidences})

        nodes = self.manager.session.query(models.Node).all()
        self.assertEqual(4, len(nodes))

        edges = self.manager.session.query(models.Edge).all()

        x = Counter((e.source.bel, e.target.bel) for e in edges)

        pfmt = 'p(HGNC:{})'
        d = {
            (pfmt.format(constants.AKT1[2]), pfmt.format(constants.EGFR[2])): 1,
            (pfmt.format(constants.EGFR[2]), pfmt.format(constants.FADD[2])): 1,
            (pfmt.format(constants.EGFR[2]), pfmt.format(constants.CASP8[2])): 1,
            (pfmt.format(constants.FADD[2]), pfmt.format(constants.CASP8[2])): 1,
            (pfmt.format(constants.AKT1[2]), pfmt.format(constants.CASP8[2])): 1,  # two way association
            (pfmt.format(constants.CASP8[2]), pfmt.format(constants.AKT1[2])): 1  # two way association
        }

        self.assertEqual(dict(x), d)

        network_edge_associations = self.manager.session.query(models.network_edge).filter_by(
            network_id=network.id).all()
        self.assertEqual({nea.edge_id for nea in network_edge_associations},
                         {edge.id for edge in edges})

        g2 = self.manager.get_graph(expected_test_simple_metadata[METADATA_NAME],
                                    expected_test_simple_metadata[METADATA_VERSION])
        self.bel_simple_reconstituted(g2)

    @mock_bel_resources
    def test_get_or_create_citation(self, mock_get):
        basic_citation = {
            CITATION_TYPE: 'PubMed',
            CITATION_NAME: 'TestCitation_basic',
            CITATION_REFERENCE: '1234AB',
        }

        full_citation = {
            CITATION_TYPE: 'Other',
            CITATION_NAME: 'TestCitation_full',
            CITATION_REFERENCE: 'CD5678',
            CITATION_DATE: '2017-04-11',
            CITATION_AUTHORS: 'Jackson M|Lajoie J'
        }

        # Create
        basic = self.manager.get_or_create_citation(**basic_citation)
        self.assertIsInstance(basic, models.Citation)
        self.assertEqual(basic.data, basic_citation)

        full = self.manager.get_or_create_citation(**full_citation)
        self.assertIsInstance(full, models.Citation)
        self.assertEqual(full.data, full_citation)

        self.manager.session.commit()

        self.assertNotEqual(basic.id, full.id)

        # Get
        reloaded_basic = self.manager.get_or_create_citation(**basic_citation)
        self.assertEqual(basic.data, reloaded_basic.data)
        self.assertEqual(basic.id, reloaded_basic.id)

        reloaded_full = self.manager.get_or_create_citation(**full_citation)
        self.assertEqual(full.data, reloaded_full.data)
        self.assertEqual(full.id, reloaded_full.id)

    @mock_bel_resources
    def test_get_or_create_evidence(self, mock_get):
        basic_citation = {
            CITATION_TYPE: 'PubMed',
            CITATION_NAME: 'TestCitation_basic',
            CITATION_REFERENCE: '1234AB',
        }

        basic_citation = self.manager.get_or_create_citation(**basic_citation)
        evidence_txt = "Yes, all the information is true!"
        evidence_data = {
            CITATION: basic_citation.data,
            EVIDENCE: evidence_txt
        }

        # Create
        evidence = self.manager.get_or_create_evidence(basic_citation, evidence_txt)
        self.assertIsInstance(evidence, models.Evidence)
        self.assertEqual(evidence.data, evidence_data)

        self.manager.session.commit()

        # Get
        reloaded_evidence = self.manager.get_or_create_evidence(basic_citation, evidence_txt)
        self.assertEqual(evidence.data, reloaded_evidence.data)
        self.assertEqual(evidence.id, reloaded_evidence.id)

    @mock_bel_resources
    def test_get_or_create_edge(self, mock_get):
        edge_data = self.simple_graph.edge[('Protein', 'HGNC', 'AKT1')][('Protein', 'HGNC', 'EGFR')]
        source_node = self.manager.get_or_create_node(self.simple_graph, ('Protein', 'HGNC', 'AKT1'))
        target_node = self.manager.get_or_create_node(self.simple_graph, ('Protein', 'HGNC', 'EGFR'))
        citation = self.manager.get_or_create_citation(**edge_data[0][CITATION])
        evidence = self.manager.get_or_create_evidence(citation, edge_data[0][EVIDENCE])
        basic_edge = {
            'graph_key': 0,
            'source': source_node,
            'target': target_node,
            'evidence': evidence,
            'bel': 'p(HGNC:AKT1) -> p(HGNC:EGFR)',
            'relation': edge_data[0][RELATION],
            'blob': pickle.dumps(edge_data[0])
        }
        source_data = source_node.data
        target_data = target_node.data
        database_data = {
            'source': {
                'node': (source_data['key'], source_data['data']),
                'key': source_data['key']
            },
            'target': {
                'node': (target_data['key'], target_data['data']),
                'key': target_data['key']
            },
            'data': {
                RELATION: edge_data[0][RELATION],
                CITATION: citation.data,
                EVIDENCE: edge_data[0][EVIDENCE],
                ANNOTATIONS: {}
            },
            'key': 0
        }

        # Create
        edge = self.manager.get_or_create_edge(**basic_edge)
        self.assertIsInstance(edge, models.Edge)
        self.assertEqual(edge.data, database_data)

        self.manager.session.commit()

        # Get
        reloaded_edge = self.manager.get_or_create_edge(**basic_edge)
        self.assertEqual(edge.data, reloaded_edge.data)
        self.assertEqual(edge.id, reloaded_edge.id)

    @mock_bel_resources
    def test_get_or_create_author(self, mock_get):
        author_name = "Jackson M"

        # Create
        author = self.manager.get_or_create_author(author_name)
        self.assertIsInstance(author, models.Author)
        self.assertEqual(author.name, author_name)

        self.manager.session.commit()

        # Get
        reloaded_author = self.manager.get_or_create_author(author_name)
        self.assertEqual(author.name, reloaded_author.name)

    @mock_bel_resources
    def test_get_or_create_modification(self, mock_get):
        node_data = self.simple_graph.node[('Protein', 'HGNC', 'FADD')]
        fusion_missing = {
            FUSION: {
                PARTNER_3P: {
                    NAMESPACE: 'HGNC',
                    NAME: 'AKT1',
                },
                RANGE_3P: {
                    FUSION_MISSING: '?',
                },
                PARTNER_5P: {
                    NAMESPACE: 'HGNC',
                    NAME: 'EGFR'
                },
                RANGE_5P: {
                    FUSION_MISSING: '?',
                }
            }
        }
        fusion_full = {
            FUSION: {
                PARTNER_3P: {
                    NAMESPACE: 'HGNC',
                    NAME: 'AKT1',
                },
                RANGE_3P: {
                    FUSION_REFERENCE: 'A',
                    FUSION_START: 'START_1',
                    FUSION_STOP: 'STOP_1',
                },
                PARTNER_5P: {
                    NAMESPACE: 'HGNC',
                    NAME: 'EGFR'
                },
                RANGE_5P: {
                    FUSION_REFERENCE: 'E',
                    FUSION_START: 'START_2',
                    FUSION_STOP: 'STOP_2',
                }
            }
        }
        hgvs = {
            KIND: HGVS,
            IDENTIFIER: 'hgvs_ident'
        }
        fragment_missing = {
            KIND: FRAGMENT,
            FRAGMENT_MISSING: '?',
        }
        fragment_full = {
            KIND: FRAGMENT,
            FRAGMENT_START: 'START_FRAG',
            FRAGMENT_STOP: 'STOP_FRAG'
        }
        gmod = {
            KIND: GMOD,
            IDENTIFIER: {
                NAMESPACE: 'test_NS',
                NAME: 'test_GMOD'
            }
        }
        pmod_simple = {
            KIND: PMOD,
            IDENTIFIER: {
                NAMESPACE: 'test_NS',
                NAME: 'test_PMOD'
            }
        }
        pmod_full = {
            KIND: PMOD,
            IDENTIFIER: {
                NAMESPACE: 'test_NS',
                NAME: 'test_PMOD_2'
            },
            PMOD_CODE: 'Tst',
            PMOD_POSITION: 12,
        }

        # Create
        node_data.update(fusion_missing)
        fusion_missing_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
        self.assertIsInstance(fusion_missing_ls, list)
        self.assertIsInstance(fusion_missing_ls[0], models.Modification)
        self.assertEqual(fusion_missing[FUSION], fusion_missing_ls[0].data['mod_data'])

        self.manager.session.add(fusion_missing_ls[0])
        self.manager.session.flush()
        self.manager.session.commit()

        # Get
        reloaded_fusion_missing_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
        self.assertEqual(fusion_missing_ls[0].id, reloaded_fusion_missing_ls[0].id)

        # Create
        node_data.update(fusion_full)
        fusion_full_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
        self.assertIsInstance(fusion_full_ls, list)
        self.assertIsInstance(fusion_full_ls[0], models.Modification)
        self.assertEqual(fusion_full[FUSION], fusion_full_ls[0].data['mod_data'])

        self.manager.session.add(fusion_full_ls[0])
        self.manager.session.flush()
        self.manager.session.commit()

        # Get
        reloaded_fusion_full_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
        self.assertEqual(fusion_full_ls[0].id, reloaded_fusion_full_ls[0].id)

        del node_data[FUSION]

        # Create
        node_data[VARIANTS] = [hgvs]
        hgvs_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
        self.assertEqual(hgvs, hgvs_ls[0].data['mod_data'])

        self.manager.session.add(fusion_full_ls[0])
        self.manager.session.flush()
        self.manager.session.commit()

        # Get
        reloaded_hgvs_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
        self.assertEqual(hgvs_ls[0].id, reloaded_hgvs_ls[0].id)

        # Create
        node_data[VARIANTS] = [fragment_missing]
        fragment_missing_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
        self.assertEqual(fragment_missing, fragment_missing_ls[0].data['mod_data'])

        self.manager.session.add(fragment_missing_ls[0])
        self.manager.session.flush()
        self.manager.session.commit()

        # Get
        reloaded_fragment_missing_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
        self.assertEqual(fragment_missing_ls[0].id, reloaded_fragment_missing_ls[0].id)

        # Create
        node_data[VARIANTS] = [fragment_full]
        fragment_full_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
        self.assertEqual(fragment_full, fragment_full_ls[0].data['mod_data'])

        self.manager.session.add(fragment_full_ls[0])
        self.manager.session.flush()
        self.manager.session.commit()

        # Get
        reloaded_fragment_full_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
        self.assertEqual(fragment_full_ls[0].id, reloaded_fragment_full_ls[0].id)

        # Create
        node_data[VARIANTS] = [gmod]
        gmod_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
        self.assertEqual(gmod, gmod_ls[0].data['mod_data'])

        self.manager.session.add(gmod_ls[0])
        self.manager.session.flush()
        self.manager.session.commit()

        # Get
        reloaded_gmod_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
        self.assertEqual(gmod_ls[0].id, reloaded_gmod_ls[0].id)

        # Create
        node_data[VARIANTS] = [pmod_simple]
        pmod_simple_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
        self.assertEqual(pmod_simple, pmod_simple_ls[0].data['mod_data'])

        self.manager.session.add(pmod_simple_ls[0])
        self.manager.session.flush()
        self.manager.session.commit()

        # Get
        reloaded_pmod_simple_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
        self.assertEqual(pmod_simple_ls[0].id, reloaded_pmod_simple_ls[0].id)

        # Create
        node_data[VARIANTS] = [pmod_full]
        pmod_full_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
        self.assertEqual(pmod_full, pmod_full_ls[0].data['mod_data'])

        self.manager.session.add(pmod_full_ls[0])
        self.manager.session.flush()
        self.manager.session.commit()

        # Get
        reloaded_pmod_full_ls = self.manager.get_or_create_modification(self.simple_graph, node_data)
        self.assertEqual(pmod_full_ls[0].id, reloaded_pmod_full_ls[0].id)

    @mock_bel_resources
    def test_get_or_create_property(self, mock_get):
        activity = {
            'data': {
                SUBJECT: {
                    EFFECT: {
                        NAME: 'pep',
                        NAMESPACE: BEL_DEFAULT_NAMESPACE
                    },
                    MODIFIER: ACTIVITY
                }
            },
            'participant': SUBJECT
        }
        translocation = {
            'data': {
                SUBJECT: {
                    EFFECT: {
                        FROM_LOC: {
                            NAME: 'host intracellular organelle',
                            NAMESPACE: GOCC_KEYWORD
                        },
                        TO_LOC: {
                            NAME: 'host outer membrane',
                            NAMESPACE: GOCC_KEYWORD
                        },
                    },
                    MODIFIER: TRANSLOCATION
                }
            },
            'participant': SUBJECT
        }
        location = {
            'data': {
                SUBJECT: {
                    LOCATION: {
                        NAMESPACE: GOCC_KEYWORD,
                        NAME: 'Herring body'
                    }
                }
            },
            'participant': SUBJECT
        }
        degradation = {
            'data': {
                SUBJECT: {
                    MODIFIER: DEGRADATION
                }
            },
            'participant': SUBJECT
        }
        edge_data = self.simple_graph.edge[('Protein', 'HGNC', 'AKT1')][('Protein', 'HGNC', 'EGFR')][0]

        # Create
        edge_data.update(activity['data'])
        activity_ls = self.manager.get_or_create_property(self.simple_graph, edge_data)
        self.assertIsInstance(activity_ls, list)
        self.assertIsInstance(activity_ls[0], models.Property)
        self.assertEqual(activity_ls[0].data, activity)

        # Get
        self.manager.session.add(activity_ls[0])
        self.manager.flush()
        self.manager.session.commit()

        reloaded_activity_ls = self.manager.get_or_create_property(self.simple_graph, edge_data)
        self.assertEqual(activity_ls[0].id, reloaded_activity_ls[0].id)

        # Create
        edge_data.update(location['data'])
        location_ls = self.manager.get_or_create_property(self.simple_graph, edge_data)
        self.assertEqual(location_ls[0].data, location)

        # Get
        self.manager.session.add(location_ls[0])
        self.manager.flush()
        self.manager.session.commit()

        reloaded_location_ls = self.manager.get_or_create_property(self.simple_graph, edge_data)
        self.assertEqual(location_ls[0].id, reloaded_location_ls[0].id)

        # Create
        edge_data.update(degradation['data'])
        degradation_ls = self.manager.get_or_create_property(self.simple_graph, edge_data)
        self.assertEqual(degradation_ls[0].data, degradation)

        # Get
        self.manager.session.add(degradation_ls[0])
        self.manager.flush()
        self.manager.session.commit()

        reloaded_degradation_ls = self.manager.get_or_create_property(self.simple_graph, edge_data)
        self.assertEqual(degradation_ls[0].id, reloaded_degradation_ls[0].id)

        # Create
        edge_data.update(translocation['data'])
        translocation_ls = self.manager.get_or_create_property(self.simple_graph, edge_data)
        self.assertEqual(translocation_ls[0].data, translocation)

        # Get
        self.manager.session.add(translocation_ls[0])
        self.manager.flush()
        self.manager.session.commit()

        source_node = self.manager.get_or_create_node(self.simple_graph, ('Protein', 'HGNC', 'AKT1'))
        target_node = self.manager.get_or_create_node(self.simple_graph, ('Protein', 'HGNC', 'EGFR'))
        citation = self.manager.get_or_create_citation(**edge_data[0][CITATION])
        evidence = self.manager.get_or_create_evidence(citation, edge_data[0][EVIDENCE])
        basic_edge = {
            'graph_key': 0,
            'source': source_node,
            'target': target_node,
            'evidence': evidence,
            'bel': 'p(HGNC:AKT1) -> p(HGNC:EGFR)',
            'relation': edge_data[0][RELATION],
            'blob': pickle.dumps(edge_data[0])
        }
        edge = self.manager.get_or_create_edge(**basic_edge)
        self.assertIn(translocation['data'], edge.data)


class TestQuery(TemporaryCacheMixin, BelReconstitutionMixin):
    """Tests that the cache can be queried"""

    def setUp(self):
        super(TestQuery, self).setUp()
        self.graph = pybel.from_path(test_bel_simple, manager=self.manager, allow_nested=True)
        self.manager.insert_graph(self.graph, store_parts=True)

    @mock_bel_resources
    def test_query_node(self, mock_get):
        akt1_dict = {
            'key': ('Protein', 'HGNC', 'AKT1'),
            'data': {
                FUNCTION: 'Protein',
                NAMESPACE: 'HGNC',
                NAME: 'AKT1'
            }
        }

        node_list = self.manager.get_node(bel='p(HGNC:AKT1)')
        self.assertEqual(len(node_list), 1)

        node_dict_list = self.manager.get_node(bel='p(HGNC:AKT1)', as_dict_list=True)
        self.assertIn(akt1_dict, node_dict_list)

        node_dict_list2 = self.manager.get_node(namespace='HG%', as_dict_list=True)
        self.assertEqual(len(node_dict_list2), 4)
        self.assertIn(akt1_dict, node_dict_list2)

        node_dict_list3 = self.manager.get_node(name='%A%', as_dict_list=True)
        self.assertEqual(len(node_dict_list3), 3)
        self.assertIn(akt1_dict, node_dict_list3)

        protein_list = self.manager.get_node(type='Protein')
        self.assertEqual(len(protein_list), 4)

    @mock_bel_resources
    def test_query_edge(self, mock_get):
        fadd_casp = {
            'source': {
                'node': (('Protein', 'HGNC', 'FADD'), {
                    FUNCTION: 'Protein',
                    NAMESPACE: 'HGNC',
                    NAME: 'FADD'
                }),
                'key': ('Protein', 'HGNC', 'FADD')
            },
            'target': {
                'node': (('Protein', 'HGNC', 'CASP8'), {
                    FUNCTION: 'Protein',
                    NAMESPACE: 'HGNC',
                    NAME: 'CASP8'
                }),
                'key': ('Protein', 'HGNC', 'CASP8')
            },
            'data': {
                RELATION: 'increases',
                ANNOTATIONS: {
                    'Species': '10116'
                },
                CITATION: {
                    CITATION_TYPE: "PubMed",
                    CITATION_NAME: "That other article from last week",
                    CITATION_REFERENCE: "123456"
                },
                EVIDENCE: "Evidence 3"
            },
            'key': 0
        }

        # bel
        edge_list = self.manager.get_edge(bel="p(HGNC:EGFR) decreases p(HGNC:FADD)")
        self.assertEqual(len(edge_list), 1)

        # relation like, data
        increased_list = self.manager.get_edge(relation='increase%', as_dict_list=True)
        self.assertEqual(len(increased_list), 2)
        self.assertIn(fadd_casp, increased_list)

        # evidence like, data
        evidence_list = self.manager.get_edge(evidence='%3%', as_dict_list=True)
        self.assertEqual(len(increased_list), 2)
        self.assertIn(fadd_casp, evidence_list)

        # no result
        empty_list = self.manager.get_edge(source='p(HGNC:EGFR)', relation='increases', as_dict_list=True)
        self.assertEqual(len(empty_list), 0)

        # source, relation, data
        source_list = self.manager.get_edge(source='p(HGNC:FADD)', relation='increases', as_dict_list=True)
        self.assertEqual(len(source_list), 1)
        self.assertIn(fadd_casp, source_list)

    @mock_bel_resources
    def test_query_citation(self, mock_get):
        citation_1 = {
            CITATION_TYPE: "PubMed",
            CITATION_NAME: "That one article from last week",
            CITATION_REFERENCE: "123455",
            CITATION_DATE: "2012-01-31",
            CITATION_AUTHORS: "Example Author|Example Author2"
        }
        citation_2 = {
            CITATION_TYPE: "PubMed",
            CITATION_NAME: "That other article from last week",
            CITATION_REFERENCE: "123456"
        }
        evidence_citation = {
            CITATION: citation_1,
            EVIDENCE: 'Evidence 1 w extra notes'
        }
        evidence_citation_2 = {
            CITATION: citation_1,
            EVIDENCE: 'Evidence 2'
        }
        evidence_citation_3 = {
            CITATION: citation_2,
            EVIDENCE: "Evidence 3"
        }

        # type
        object_list = self.manager.get_citation(type='PubMed')
        self.assertEqual(len(object_list), 2)

        # type, reference, data
        reference_list = self.manager.get_citation(type='PubMed', reference='123456', as_dict_list=True)
        self.assertEqual(len(reference_list), 1)
        self.assertIn(citation_2, reference_list)

        # author
        author_list = self.manager.get_citation(author="Example%")
        self.assertEqual(len(author_list), 1)

        # author, data
        author_dict_list = self.manager.get_citation(author="Example Author", as_dict_list=True)
        self.assertIn(citation_1, author_dict_list)

        # author list, data
        author_dict_list2 = self.manager.get_citation(author=["Example Author", "Example Author2"], as_dict_list=True)
        self.assertIn(citation_1, author_dict_list2)

        # type, name, data
        name_dict_list = self.manager.get_citation(type='PubMed', name="That other article from last week",
                                                   as_dict_list=True)
        self.assertEqual(len(name_dict_list), 1)
        self.assertIn(citation_2, name_dict_list)

        # type, name like, data
        name_dict_list2 = self.manager.get_citation(type='PubMed', name="%article from%", as_dict_list=True)
        self.assertEqual(len(name_dict_list2), 2)
        self.assertIn(citation_1, name_dict_list2)
        self.assertIn(citation_2, name_dict_list2)

        # type, name, evidence, data
        evidence_dict_list = self.manager.get_citation(type='PubMed', name="That other article from last week",
                                                       evidence=True, as_dict_list=True)
        self.assertEqual(len(name_dict_list), 1)
        self.assertIn(evidence_citation_3, evidence_dict_list)

        # type, evidence like, data
        evidence_dict_list2 = self.manager.get_citation(type='PubMed', evidence_text='%Evi%', as_dict_list=True)
        self.assertEqual(len(evidence_dict_list2), 3)
        self.assertIn(evidence_citation, evidence_dict_list2)
        self.assertIn(evidence_citation_2, evidence_dict_list2)
        self.assertIn(evidence_citation_3, evidence_dict_list2)

    @mock_bel_resources
    def test_query_network(self, mock_get):
        pass

@unittest.skip('Feature not started yet')
class TestFilter(TemporaryCacheMixin, BelReconstitutionMixin):
    """Tests that a graph can be reconstructed from the edge and node relational tables in the database

    1. Load graph (test BEL 1 or test thorough)
    2. Add sentinel annotation to ALL edges
    3. Store graph
    4. Query for all edges with sentinel annotation
    5. Compare to original graph
    """

    def setUp(self):
        super(TestFilter, self).setUp()
        self.graph = pybel.from_path(test_bel_thorough, manager=self.manager, allow_nested=True)

    @mock_bel_resources
    def test_database_edge_filter(self, mock_get):
        self.help_database_edge_filter(test_bel_simple, self.bel_simple_reconstituted)

    @mock_bel_resources
    def test_database_edge_filter(self, mock_get):
        self.help_database_edge_filter(test_bel_thorough, self.bel_thorough_reconstituted)

    def help_database_edge_filter(self, path, compare, annotation_tag='MeSHDisease', value_tag='Arm Injuries'):
        """Helps to test the graph that is created by a specific annotation.

        :param path: Path to the test BEL file.
        :type path: str
        :param compare: Method that should be used to compare the original and resulting graph.
        :type compare:
        :param annotation_tag: Annotation that marks the nodes with an annotation.
        :type annotation_tag: str
        :param value_tag: Annotation value for the given sentinel_annotation.
        :type value_tag: str
        """
        original = pybel.from_path(path)

        compare(original)

        for u, v, k in original.edges(keys=True):
            original.edge[u][v][k][annotation_tag] = value_tag

        self.manager.insert_graph(original, store_parts=True)

        reloaded = self.manager.rebuild_by_edge_filter(**{ANNOTATIONS: {annotation_tag: value_tag}})

        for u, v, k in reloaded.edges(keys=True):
            del reloaded.edge[u][v][k][annotation_tag]

        compare(reloaded, check_metadata=False)
