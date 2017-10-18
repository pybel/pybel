import os
import tempfile
from collections import Counter

import pybel
from pybel.constants import *
from pybel.manager import models, Manager
from pybel.utils import hash_dump
from tests import constants
from tests.constants import (
    BelReconstitutionMixin,
    test_bel_simple,
    expected_test_simple_metadata,
)
from tests.mocks import mock_bel_resources


class TestEdgeStore(BelReconstitutionMixin):
    """Tests that the cache can be queried"""

    def setUp(self):
        self.test_connection = os.environ.get('PYBEL_TEST_CONNECTION')

        if self.test_connection:
            self.connection = self.test_connection
        else:
            self.fd, self.path = tempfile.mkstemp()
            self.connection = 'sqlite:///' + self.path

        log.info('Test generated connection string %s', self.connection)

        self.manager = Manager(connection=self.connection)
        self.manager.create_all()

        self.graph = self.setup_graph()
        self.network = self.setup_insert()

    def tearDown(self):
        self.manager.session.close()

        if not self.test_connection:
            os.close(self.fd)
            os.remove(self.path)

    @mock_bel_resources
    def setup_graph(self, mock):
        return pybel.from_path(path=test_bel_simple, manager=self.manager, allow_nested=True)

    def setup_insert(self):
        return self.manager.insert_graph(self.graph)

    def test_citations(self):
        citations = self.manager.session.query(models.Citation).all()
        self.assertEqual(2, len(citations), msg='Citations: {}'.format(citations))

        citation_references = {'123455', '123456'}
        self.assertEqual(citation_references, {
            citation.reference
            for citation in citations
            })

    def test_authors(self):
        authors = {'Example Author', 'Example Author2'}
        self.assertEqual(authors, {
            author.name
            for author in self.manager.session.query(models.Author).all()
            })

    def test_evidences(self):
        evidences = self.manager.session.query(models.Evidence).all()
        self.assertEqual(3, len(evidences))

        evidences_texts = {'Evidence 1 w extra notes', 'Evidence 2', 'Evidence 3'}
        self.assertEqual(evidences_texts, {
            evidence.text
            for evidence in evidences
            })

    def test_nodes(self):
        nodes = self.manager.session.query(models.Node).all()
        self.assertEqual(4, len(nodes))

    def test_edges(self):
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
            network_id=self.network.id).all()

        self.assertEqual(
            {network_edge_association.edge_id for network_edge_association in network_edge_associations},
            {edge.id for edge in edges}
        )

    def test_reconstitute(self):
        g2 = self.manager.get_network_by_name_version(
            expected_test_simple_metadata[METADATA_NAME],
            expected_test_simple_metadata[METADATA_VERSION]
        )
        self.bel_simple_reconstituted(g2)

    @mock_bel_resources
    def test_get_or_create_properties(self, mock_get):
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
                        NAME: 'intine'
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

        edge_data = self.graph.edge[(PROTEIN, 'HGNC', 'AKT1')][(PROTEIN, 'HGNC', 'EGFR')][0]

        activity_hash = hash_dump({
            'participant': SUBJECT,
            'modifier': ACTIVITY,
            'effectNamespace': BEL_DEFAULT_NAMESPACE,
            'effectName': 'pep'
        })
        translocation_from_hash = hash_dump({
            'participant': SUBJECT,
            'modifier': TRANSLOCATION,
            'relativeKey': FROM_LOC,
            'namespaceEntry': self.manager.get_namespace_entry(GOCC_LATEST, 'host intracellular organelle')
        })
        translocation_to_hash = hash_dump({
            'participant': SUBJECT,
            'modifier': TRANSLOCATION,
            'relativeKey': TO_LOC,
            'namespaceEntry': self.manager.get_namespace_entry(GOCC_LATEST, 'host outer membrane')
        })
        location_hash = hash_dump({
            'participant': SUBJECT,
            'modifier': LOCATION,
            'namespaceEntry': self.manager.get_namespace_entry(GOCC_LATEST, 'intine')
        })
        degradation_hash = hash_dump({
            'participant': SUBJECT,
            'modifier': DEGRADATION
        })

        # Create
        edge_data.update(activity['data'])
        activity_ls = self.manager.get_or_create_properties(self.graph, edge_data)
        self.assertIsInstance(activity_ls, list)
        self.assertIsInstance(activity_ls[0], models.Property)
        self.assertEqual(activity_ls[0].data, activity)

        # Activity was stored with hash in object cache
        self.assertIn(activity_hash, self.manager.object_cache_property)
        self.assertEqual(1, len(self.manager.object_cache_property.keys()))

        reloaded_activity_ls = self.manager.get_or_create_properties(self.graph, edge_data)
        self.assertEqual(activity_ls, reloaded_activity_ls)

        # No new activity object was created
        self.assertEqual(1, len(self.manager.object_cache_property.keys()))

        # Create
        edge_data.update(location['data'])
        location_ls = self.manager.get_or_create_properties(self.graph, edge_data)
        self.assertEqual(location_ls[0].data, location)

        self.assertIn(location_hash, self.manager.object_cache_property)
        self.assertEqual(2, len(self.manager.object_cache_property.keys()))

        # Get
        reloaded_location_ls = self.manager.get_or_create_properties(self.graph, edge_data)
        self.assertEqual(location_ls, reloaded_location_ls)

        # No second location property object was created
        self.assertEqual(2, len(self.manager.object_cache_property.keys()))

        # Create
        edge_data.update(degradation['data'])
        degradation_ls = self.manager.get_or_create_properties(self.graph, edge_data)
        self.assertEqual(degradation_ls[0].data, degradation)

        self.assertIn(degradation_hash, self.manager.object_cache_property)
        self.assertEqual(3, len(self.manager.object_cache_property.keys()))

        # Get
        reloaded_degradation_ls = self.manager.get_or_create_properties(self.graph, edge_data)
        self.assertEqual(degradation_ls, reloaded_degradation_ls)

        # No second degradation property object was created
        self.assertEqual(3, len(self.manager.object_cache_property.keys()))

        # Create
        edge_data.update(translocation['data'])
        self.manager.get_or_create_properties(self.graph, edge_data)

        # 2 translocation objects addaed
        self.assertEqual(5, len(self.manager.object_cache_property.keys()))
        self.assertIn(translocation_from_hash, self.manager.object_cache_property)
        self.assertIn(translocation_to_hash, self.manager.object_cache_property)

        # @mock_bel_resources
        # def test_get_or_create_edge(self, mock_get):
        #
        #     edge_data = self.graph.edge[(PROTEIN, 'HGNC', 'AKT1')][(PROTEIN, 'HGNC', 'EGFR')]
        #     source_node = self.manager.get_or_create_node(self.graph, (PROTEIN, 'HGNC', 'AKT1'))
        #     target_node = self.manager.get_or_create_node(self.graph, (PROTEIN, 'HGNC', 'EGFR'))
        #     citation = self.manager.get_or_create_citation(**edge_data[0][CITATION])
        #     evidence = self.manager.get_or_create_evidence(citation, edge_data[0][EVIDENCE])
        #     properties = self.manager.get_or_create_properties(self.graph, edge_data[0])
        #     annotations = []
        #     edge_hash = hash_edge(u=source_node, v=target_node, k=0, d=edge_data)
        #     basic_edge = {
        #         'source': source_node,
        #         'target': target_node,
        #         'edge_hash': edge_hash,
        #         'evidence': evidence,
        #         'bel': 'p(HGNC:AKT1) -> p(HGNC:EGFR)',
        #         'relation': edge_data[0][RELATION],
        #         'properties': properties,
        #         'annotations': annotations,
        #         'blob': dumps(edge_data[0])
        #     }
        #     database_data = {
        #         'source': source_node.to_json(),
        #         'target': target_node.to_json(),
        #         'data': {
        #             RELATION: edge_data[0][RELATION],
        #             CITATION: citation.to_json(),
        #             EVIDENCE: evidence.to_json(),
        #             ANNOTATIONS: {}
        #         },
        #         'key': 0
        #     }
        #
        #     # Create
        #     edge = self.manager.get_or_create_edge(**basic_edge)
        #     self.assertIsInstance(edge, models.Edge)
        #     self.assertEqual(edge.to_json(), database_data)
        #
        #     self.assertIn(edge_hash, self.manager.object_cache_edge)
        #
        #     # Get
        #     reloaded_edge = self.manager.get_or_create_edge(**basic_edge)
        #     self.assertEqual(edge.to_json(), reloaded_edge.to_json())
        #     self.assertEqual(edge, reloaded_edge)
        #
        #     self.assertEqual(1, len(self.manager.object_cache_edge.keys()))

    @mock_bel_resources
    def test_get_or_create_modification(self, mock_get):
        node_data = self.graph.node[(PROTEIN, 'HGNC', 'FADD')]
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

        hgnc_url = self.graph.namespace_url['HGNC']
        AKT1_object = self.manager.get_namespace_entry(url=hgnc_url, name='AKT1')
        EGFR_object = self.manager.get_namespace_entry(url=hgnc_url, name='EGFR')

        fusion_missing_hash = hash_dump({
            'modType': FUSION,
            'p3Partner': AKT1_object,
            'p5Partner': EGFR_object,
            'p3Missing': '?',
            'p5Missing': '?',
        })
        fusion_full_hash = hash_dump({
            'modType': FUSION,
            'p3Partner': AKT1_object,
            'p5Partner': EGFR_object,
            'p3Reference': 'A',
            'p3Start': 'START_1',
            'p3Stop': 'STOP_1',
            'p5Reference': 'E',
            'p5Start': 'START_2',
            'p5Stop': 'STOP_2'
        })
        hgvs_hash = hash_dump({
            'modType': HGVS,
            'variantString': 'hgvs_ident'
        })
        fragment_missing_hash = hash_dump({
            'modType': FRAGMENT,
            'p3Missing': '?'
        })
        fragment_full_hash = hash_dump({
            'modType': FRAGMENT,
            'p3Start': 'START_FRAG',
            'p3Stop': 'STOP_FRAG'
        })
        gmod_hash = hash_dump({
            'modType': GMOD,
            'modNamespace': 'test_NS',
            'modName': 'test_GMOD'
        })
        pmod_simple_hash = hash_dump({
            'modType': PMOD,
            'modNamespace': 'test_NS',
            'modName': 'test_PMOD',
            'aminoA': None,
            'position': None
        })
        pmod_full_hash = hash_dump({
            'modType': PMOD,
            'modNamespace': 'test_NS',
            'modName': 'test_PMOD_2',
            'aminoA': 'Tst',
            'position': 12
        })

        # Create
        node_data.update(fusion_missing)
        fusion_missing_ls = self.manager.get_or_create_modification(self.graph, node_data)
        self.assertIsInstance(fusion_missing_ls, list)
        self.assertIsInstance(fusion_missing_ls[0], models.Modification)
        self.assertEqual(fusion_missing[FUSION], fusion_missing_ls[0].data['mod_data'])

        self.assertIn(fusion_missing_hash, self.manager.object_cache_modification)

        # Get
        reloaded_fusion_missing_ls = self.manager.get_or_create_modification(self.graph, node_data)
        self.assertEqual(fusion_missing_ls, reloaded_fusion_missing_ls)

        # Create
        node_data.update(fusion_full)
        fusion_full_ls = self.manager.get_or_create_modification(self.graph, node_data)
        self.assertIsInstance(fusion_full_ls, list)
        self.assertIsInstance(fusion_full_ls[0], models.Modification)
        self.assertEqual(fusion_full[FUSION], fusion_full_ls[0].data['mod_data'])

        self.assertIn(fusion_full_hash, self.manager.object_cache_modification)

        # Get
        reloaded_fusion_full_ls = self.manager.get_or_create_modification(self.graph, node_data)
        self.assertEqual(fusion_full_ls, reloaded_fusion_full_ls)

        del node_data[FUSION]

        # Create
        node_data[VARIANTS] = [hgvs]
        hgvs_ls = self.manager.get_or_create_modification(self.graph, node_data)
        self.assertEqual(hgvs, hgvs_ls[0].data['mod_data'])

        self.assertIn(hgvs_hash, self.manager.object_cache_modification)

        # Get
        reloaded_hgvs_ls = self.manager.get_or_create_modification(self.graph, node_data)
        self.assertEqual(hgvs_ls, reloaded_hgvs_ls)

        # Create
        node_data[VARIANTS] = [fragment_missing]
        fragment_missing_ls = self.manager.get_or_create_modification(self.graph, node_data)
        self.assertEqual(fragment_missing, fragment_missing_ls[0].data['mod_data'])

        self.assertIn(fragment_missing_hash, self.manager.object_cache_modification)

        # Get
        reloaded_fragment_missing_ls = self.manager.get_or_create_modification(self.graph, node_data)
        self.assertEqual(fragment_missing_ls, reloaded_fragment_missing_ls)

        # Create
        node_data[VARIANTS] = [fragment_full]
        fragment_full_ls = self.manager.get_or_create_modification(self.graph, node_data)
        self.assertEqual(fragment_full, fragment_full_ls[0].data['mod_data'])

        self.assertIn(fragment_full_hash, self.manager.object_cache_modification)

        # Get
        reloaded_fragment_full_ls = self.manager.get_or_create_modification(self.graph, node_data)
        self.assertEqual(fragment_full_ls, reloaded_fragment_full_ls)

        # Create
        node_data[VARIANTS] = [gmod]
        gmod_ls = self.manager.get_or_create_modification(self.graph, node_data)
        self.assertEqual(gmod, gmod_ls[0].data['mod_data'])

        self.assertIn(gmod_hash, self.manager.object_cache_modification)

        # Get
        reloaded_gmod_ls = self.manager.get_or_create_modification(self.graph, node_data)
        self.assertEqual(gmod_ls, reloaded_gmod_ls)

        # Create
        node_data[VARIANTS] = [pmod_simple]
        pmod_simple_ls = self.manager.get_or_create_modification(self.graph, node_data)
        self.assertEqual(pmod_simple, pmod_simple_ls[0].data['mod_data'])

        self.assertIn(pmod_simple_hash, self.manager.object_cache_modification)

        # Get
        reloaded_pmod_simple_ls = self.manager.get_or_create_modification(self.graph, node_data)
        self.assertEqual(pmod_simple_ls, reloaded_pmod_simple_ls)

        # Create
        node_data[VARIANTS] = [pmod_full]
        pmod_full_ls = self.manager.get_or_create_modification(self.graph, node_data)
        self.assertEqual(pmod_full, pmod_full_ls[0].data['mod_data'])

        self.assertIn(pmod_full_hash, self.manager.object_cache_modification)

        # Get
        reloaded_pmod_full_ls = self.manager.get_or_create_modification(self.graph, node_data)
        self.assertEqual(pmod_full_ls, reloaded_pmod_full_ls)

        # Every modification was added only once to the object cache
        self.assertEqual(8, len(self.manager.object_cache_modification.keys()))
