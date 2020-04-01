# -*- coding: utf-8 -*-

"""Tests for node utilities."""

import unittest

from pybel import BELGraph
from pybel.constants import INCREASES
from pybel.dsl import ComplexAbundance as g, CompositeAbundance as c, Protein, Reaction
from pybel.examples.various_example import adp, atp, glucose, glucose_6_phosphate, hk1, phosphate, single_reaction_graph
from pybel.struct.node_utils import flatten_list_abundance, reaction_cartesian_expansion


class TestNodeUtils(unittest.TestCase):
    """Test node utilities."""

    def test_flatten_complex(self):
        """Test flattening a nested complex."""
        p1, p2, p3 = (Protein('N', str(i + 1)) for i in range(3))

        pairs = [
            # Mainly complexes
            (g([p1, p2, p3]), g([p1, p2, p3])),  # no nesting
            (g([p1, p2, p3]), g([g([p1, p2]), p3])),  # one nesting
            (g([p1, p2, p3]), g([g([p1]), p2, p3])),  # one nesting
            (g([p1, p2, p3]), g([g([p1]), g([p2]), p3])),  # one nesting
            # Mainly composites
            (c([p1, p2, p3]), c([p1, p2, p3])),  # no nesting
            (c([p1, p2, p3]), c([c([p1, p2]), p3])),  # one nesting
            (c([p1, p2, p3]), c([c([p1]), p2, p3])),  # one nesting
            (c([p1, p2, p3]), c([c([p1]), c([p2]), p3])),  # one nesting
            # TODO: mixtures of composites and complexes?
        ]

        for expected, source in pairs:
            self.assertEqual(expected, flatten_list_abundance(source))

    def test_flatten_reaction(self):
        """Test flattening a reaction."""
        single_reaction_graph_copy = single_reaction_graph.copy()

        self.assertEqual(single_reaction_graph_copy.number_of_nodes(), 7)
        self.assertEqual(single_reaction_graph_copy.number_of_edges(), 7)

        reaction_cartesian_expansion(single_reaction_graph_copy)

        self.assertEqual(single_reaction_graph_copy.number_of_nodes(), 6)
        self.assertEqual(single_reaction_graph_copy.number_of_edges(), 8)

        pairs = [
            (glucose, INCREASES, glucose_6_phosphate),
            (glucose, INCREASES, adp),
            (hk1, INCREASES, glucose_6_phosphate),
            (hk1, INCREASES, adp),
            (atp, INCREASES, glucose_6_phosphate),
            (atp, INCREASES, adp),
            (phosphate, INCREASES, glucose_6_phosphate),
            (phosphate, INCREASES, adp),
        ]

        for source, target, data in single_reaction_graph_copy.edges(data=True):
            self.assertIn((source, INCREASES, target), pairs)

    def test_flatten_reaction_2(self):
        """Test flattening a qualified reaction."""
        node_increases_reaction_graph = BELGraph()

        glycolisis_step_1 = Reaction(reactants=[glucose, hk1, atp], products=[glucose_6_phosphate, adp, hk1])

        node_increases_reaction_graph.add_increases(glucose_6_phosphate, glycolisis_step_1, citation='X', evidence='X')

        self.assertEqual(node_increases_reaction_graph.number_of_nodes(), 6)
        self.assertEqual(node_increases_reaction_graph.number_of_edges(), 7)

        reaction_cartesian_expansion(node_increases_reaction_graph)

        self.assertEqual(node_increases_reaction_graph.number_of_nodes(), 5)
        # TODO Fix so unqualified duplicate edges are not created (it should be the 8 edges below)
        self.assertEqual(node_increases_reaction_graph.number_of_edges(), 12)

        # pairs = [
        #     (glucose, INCREASES, glucose_6_phosphate),
        #     (glucose, INCREASES, adp),
        #     (hk1, INCREASES, glucose_6_phosphate),
        #     (hk1, INCREASES, adp),
        #     (atp, INCREASES, glucose_6_phosphate),
        #     (atp, INCREASES, adp),
        #     (phosphate, INCREASES, glucose_6_phosphate),
        #     (phosphate, INCREASES, adp),
        # ]
        #
        # for source, target, data in node_increases_reaction_graph.edges(data=True):
        #     self.assertIn((source, INCREASES, target), pairs)

    def test_flatten_reaction_3(self):
        """Test flattening a graph containing 2 reactions connected to each other."""
        two_reactions_graph = BELGraph()

        reaction_1 = Reaction(reactants=[glucose, atp], products=hk1)
        reaction_2 = Reaction(reactants=glucose_6_phosphate, products=adp)

        two_reactions_graph.add_increases(reaction_1, reaction_2, citation='X', evidence='X')

        self.assertEqual(two_reactions_graph.number_of_nodes(), 7)
        self.assertEqual(two_reactions_graph.number_of_edges(), 6)

        reaction_cartesian_expansion(two_reactions_graph)

        # TODO Fix so unqualified duplicate edges are not created (it should be the 6 edges below)
        self.assertEqual(two_reactions_graph.number_of_nodes(), 5)
        self.assertEqual(two_reactions_graph.number_of_edges(), 8)
