# -*- coding: utf-8 -*-

"""Tests for importing SBGN-ML."""

import os
import unittest

from pybel import BELGraph, BaseEntity, constants as pc, dsl
from pybel.io.sbgnml import convert_sbgn, parse_sbgn

HERE = os.path.abspath(os.path.dirname(__file__))
TEST_PATH = os.path.join(HERE, 'spike_test.xml')

CGP42112A_NAME = '(2S,3S)-2-[[(2S)-1-[(2S)-2-[[(2S)-6-[[(2S)-5-(Diaminomethylideneamino)-2-(phenylmethoxycarbonylamino)pentanoyl]amino]-2-[[(2S)-3-(4-hydroxyphenyl)-2-(pyridine-3-carbonylamino)propanoyl]amino]hexanoyl]amino]-3-(1H-imidazol-5-yl)propanoyl]pyrrolidine-2-carbonyl]amino]-3-methylpentanoic acid'

grounding_map = {
    'angiotensin I-9': ('chebi', '80128', 'angiotensin (1-9)'),
    'angiotensin I-7': ('chebi', '55438', 'Ile(5)-angiotensin II (1-7)'),
    'SPIKE': ('uniprot', 'P0DTC2', 'SPIKE_SARS2'),
    'CGP42112A': ('pubchem.compound', '123794', CGP42112A_NAME),
}
ren = dsl.Protein(
    namespace='hgnc',
    identifier='9958',
    name='REN',
)
agt = dsl.Protein(
    namespace='hgnc',
    identifier='333',
    name='AGT',
)
angiotensin_1 = dsl.Abundance(
    namespace='chebi',
    identifier='2718',
    name='angiotensin I',
)
angiotensin_1_9 = dsl.Abundance(
    namespace='chebi',
    identifier='80128',
    name='angiotensin (1-9)',
)
angiotensin_1_7 = dsl.Abundance(
    namespace='chebi',
    identifier='55438',
    name='Ile(5)-angiotensin II (1-7)',
)
angiotensin_2 = dsl.Abundance(
    namespace='chebi',
    identifier='48432',
    name='angiotensin II',
)
angiotensin_production = dsl.Reaction(agt, angiotensin_1)
angiotensin_1_cleavage = dsl.Reaction(angiotensin_1, angiotensin_2)
angiotensin_1_cleavage_1_9 = dsl.Reaction(angiotensin_1, angiotensin_1_9)
angiotensin_2_cleavage_1_7 = dsl.Reaction(angiotensin_2, angiotensin_1_7)
angiotensin_1_9_cleavage = dsl.Reaction(angiotensin_1_9, angiotensin_1_7)

calcitriol = dsl.Abundance(
    namespace='chebi',
    identifier='17823',
    name='calcitriol',
)
losartan = dsl.Abundance(
    namespace='chebi',
    identifier='6541',
    name='losartan',
)
lisinopril = dsl.Abundance(
    namespace='chebi',
    identifier='43755',
    name='lisinopril',
)
CGP42112A = dsl.Abundance(
    namespace='pubchem.compound',
    identifier='123794',
    name='CGP42112A_NAME',
)
ace = dsl.Protein(
    namespace='hgnc',
    identifier='2707',
    name='ACE',
)
ace2 = dsl.Protein(
    namespace='hgnc',
    identifier='13557',
    name='ACE2',
)
spike = dsl.Protein(
    namespace='uniprot',
    identifier='P0DTC2',
    name='SPIKE_SARS2',
)
agtr1 = dsl.Protein(
    namespace='hgnc',
    identifier='336',
    name='AGTR1'
)
agtr2 = dsl.Protein(
    namespace='hgnc',
    identifier='338',
    name='AGTR2'
)
mas1 = dsl.Protein(
    namespace='hgnc',
    identifier='6899',
    name='MAS1'
)

blood_pressure = dsl.Pathology(
    namespace='efo',
    identifier='0004325',
    name='blood pressure',
)


class TestSBGNML(unittest.TestCase):
    """Tests for importing SBGN-ML."""

    def assert_edge_type(self, graph: BELGraph, source: BaseEntity, target: BaseEntity, relation: str) -> None:
        self.assertIn(source, graph)
        self.assertIn(target, graph)
        self.assertIn(
            target, graph.edges[source],
            msg=f'Missing edge from {source} to {target}',
        )
        edge_data = list(graph.edges[source][target].values())[0]
        self.assertEqual(relation, edge_data[pc.RELATION])

    def test_spike(self):
        """Test importing the ACE2/Spike protein file.

        .. seealso:: http://web.newteditor.org/?URL=https://cannin.github.io/covid19-sbgn/Role_of_spike_ACE2_interaction_in_pulmonary_blood_pressure_regulation_v3.xml.sbgn
        """
        sbgn = parse_sbgn(TEST_PATH, grounding_map=grounding_map)
        self.assertIsNotNone(sbgn)

        graph = convert_sbgn(sbgn)

        self.assertIn(losartan, graph)
        self.assertIn(lisinopril, graph)
        self.assertIn(ace, graph)
        self.assertIn(ace2, graph)
        self.assertIn(angiotensin_1, graph)
        self.assertIn(angiotensin_1_7, graph)
        self.assertIn(angiotensin_1_9, graph)
        self.assertIn(angiotensin_2, graph)
        self.assertIn(spike, graph)

        self.assert_edge_type(graph, calcitriol, ren.get_rna(), pc.DECREASES)
        self.assert_edge_type(graph, ren, angiotensin_production, pc.DIRECTLY_INCREASES)

        self.assert_edge_type(graph, ace, angiotensin_1_cleavage, pc.DIRECTLY_INCREASES)
        self.assert_edge_type(graph, ace, angiotensin_1_9_cleavage, pc.DIRECTLY_INCREASES)
        self.assert_edge_type(graph, ace2, angiotensin_1_cleavage_1_9, pc.DIRECTLY_INCREASES)
        self.assert_edge_type(graph, ace2, angiotensin_2_cleavage_1_7, pc.DIRECTLY_INCREASES)

        self.assert_edge_type(graph, spike, ace2, pc.DIRECTLY_INCREASES)

        self.assert_edge_type(graph, angiotensin_2, agtr1, pc.DIRECTLY_INCREASES)
        self.assert_edge_type(graph, angiotensin_2, agtr2, pc.DIRECTLY_INCREASES)
        self.assert_edge_type(graph, angiotensin_1_7, mas1, pc.DIRECTLY_INCREASES)

        self.assert_edge_type(graph, lisinopril, ace, pc.DIRECTLY_INCREASES)
        self.assert_edge_type(graph, losartan, ace2, pc.DIRECTLY_INCREASES)
        self.assert_edge_type(graph, losartan, agtr1, pc.DIRECTLY_INCREASES)
        self.assert_edge_type(graph, CGP42112A, agtr2, pc.DIRECTLY_INCREASES)

        self.assert_edge_type(graph, agtr1, blood_pressure, pc.DIRECTLY_INCREASES)
        self.assert_edge_type(graph, agtr2, blood_pressure, pc.DIRECTLY_DECREASES)
        self.assert_edge_type(graph, mas1, blood_pressure, pc.DIRECTLY_DECREASES)
