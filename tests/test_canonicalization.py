# -*- coding: utf-8 -*-

import unittest
from uuid import uuid4

from pybel import BELGraph
from pybel.canonicalize import canonicalize_edge, fusion_range_to_bel, variant_to_bel
from pybel.constants import BEL_DEFAULT_NAMESPACE, INCREASES, KIND, MODIFIER
from pybel.dsl import *
from pybel.dsl.edges import extracellular, intracellular


class TestCanonicalize(unittest.TestCase):
    def test_variant_to_bel_key_error(self):
        with self.assertRaises(Exception):
            variant_to_bel({})

    def test_variant_to_bel_value_error(self):
        with self.assertRaises(ValueError):
            variant_to_bel({KIND: 'nope'})

    def test_canonicalize_variant(self):
        self.assertEqual('var(p.Val600Glu)', variant_to_bel(hgvs('p.Val600Glu')))
        self.assertEqual('pmod(Ph)', variant_to_bel(pmod('Ph')))
        self.assertEqual('pmod(TEST:Ph)', variant_to_bel(pmod('Ph', namespace='TEST')))
        self.assertEqual('pmod(TEST:Ph, Ser)', variant_to_bel(pmod('Ph', namespace='TEST', code='Ser')))
        self.assertEqual('pmod(TEST:Ph, Ser, 5)', variant_to_bel(pmod('Ph', namespace='TEST', code='Ser', position=5)))
        self.assertEqual('pmod(GO:"protein phosphorylation", Thr, 308)',
                         variant_to_bel(pmod(name='protein phosphorylation', namespace='GO', code='Thr', position=308)))

        self.assertEqual('gmod(Me)', variant_to_bel(gmod('Me')))
        self.assertEqual('gmod(TEST:Me)', variant_to_bel(gmod('Me', namespace='TEST')))
        self.assertEqual('gmod(GO:"DNA Methylation")', variant_to_bel(gmod('DNA Methylation', namespace='GO')))

    def test_canonicalize_fusion_range(self):
        self.assertEqual('p.1_15', fusion_range_to_bel(fusion_range('p', 1, 15)))
        self.assertEqual('p.*_15', fusion_range_to_bel(fusion_range('p', '*', 15)))


class TestCanonicalizeEdge(unittest.TestCase):
    """This class houses all testing for the canonicalization of edges such that the relation/modifications can be used
    as a second level hash"""

    def setUp(self):
        self.g = BELGraph()
        self.u = self.g.add_node_from_data(protein(name='u', namespace='TEST'))
        self.v = self.g.add_node_from_data(protein(name='v', namespace='TEST'))
        self.key = 0

    def get_data(self, k):
        return self.g.edge[self.u][self.v][k]

    def add_edge(self, subject_modifier=None, object_modifier=None, annotations=None):
        self.key += 1

        self.g.add_qualified_edge(
            self.u,
            self.v,
            relation=INCREASES,
            evidence=str(uuid4()),
            citation=str(uuid4()),
            subject_modifier=subject_modifier,
            object_modifier=object_modifier,
            annotations=annotations,
            key=self.key
        )

        return canonicalize_edge(self.get_data(self.key))

    def test_failure(self):
        with self.assertRaises(ValueError):
            self.add_edge(subject_modifier={MODIFIER: 'nope'})


    def test_canonicalize_edge_info(self):
        c1 = self.add_edge(
            annotations={
                'Species': '9606'
            }
        )

        c2 = self.add_edge(
            annotations={
                'Species': '9606'
            }
        )

        c3 = self.add_edge(
            subject_modifier=activity('tport'),
        )

        c4 = self.add_edge(
            subject_modifier=activity('tport', namespace=BEL_DEFAULT_NAMESPACE),
        )

        self.assertEqual(c1, c2)
        self.assertNotEqual(c1, c3)
        self.assertEqual(c3, c4)

    def test_subject_degradation_location(self):
        self.assertEqual(
            self.add_edge(
                subject_modifier=degradation()
            ),
            self.add_edge(
                subject_modifier=degradation()
            )
        )

        self.assertEqual(
            self.add_edge(
                subject_modifier=degradation(location=entity(name='somewhere', namespace='GOCC'))
            ),
            self.add_edge(
                subject_modifier=degradation(location=entity(name='somewhere', namespace='GOCC'))
            )
        )

        self.assertNotEqual(
            self.add_edge(
                subject_modifier=degradation()
            ),
            self.add_edge(
                subject_modifier=degradation(location=entity(name='somewhere', namespace='GOCC'))
            )
        )

    def test_translocation(self):
        self.assertEqual(
            self.add_edge(subject_modifier=secretion()),
            self.add_edge(subject_modifier=secretion()),
        )

        self.assertEqual(
            self.add_edge(subject_modifier=secretion()),
            self.add_edge(subject_modifier=translocation(from_loc=intracellular, to_loc=extracellular)),
        )
