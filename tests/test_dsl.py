# -*- coding: utf-8 -*-

"""Tests for the internal DSL."""

import unittest

import pybel.constants as pc
from pybel import BELGraph
from pybel.constants import NAME
from pybel.dsl import (
    Abundance,
    ComplexAbundance,
    CompositeAbundance,
    EnumeratedFusionRange,
    Fragment,
    Gene,
    GeneFusion,
    ListAbundanceEmptyException,
    MissingFusionRange,
    Protein,
    Reaction,
    ReactionEmptyException,
)
from pybel.language import Entity
from pybel.testing.utils import n
from pybel.tokens import parse_result_to_dsl
from pybel.utils import ensure_quotes


class TestDSL(unittest.TestCase):
    """Tests for the internal DSL."""

    def test_add_robust_node(self):
        """Test adding a node with both a name and identifier."""
        graph = BELGraph()
        namespace, name, identifier = n(), n(), n()
        node = Protein(namespace=namespace, name=name, identifier=identifier)

        graph.add_node_from_data(node)
        self.assertIn(node, graph)

    def test_add_identified_node(self):
        """Test what happens when a node with only an identifier is added to a graph."""
        graph = BELGraph()
        namespace, identifier = n(), n()
        node = Protein(namespace=namespace, identifier=identifier)
        self.assertNotIn(NAME, node)

        graph.add_node_from_data(node)
        self.assertIn(node, graph)

    def test_add_named_node(self):
        """Test adding a named node to a BEL graph."""
        graph = BELGraph()
        namespace, name = n(), n()
        node = Protein(namespace=namespace, name=name)

        graph.add_node_from_data(node)
        self.assertIn(node, graph)

    def test_missing_information(self):
        """Test that entity and abundance functions raise on missing name/identifier."""
        with self.assertRaises(ValueError):
            Entity(namespace="test")

        with self.assertRaises(ValueError):
            Protein(namespace="test")

        with self.assertRaises(ValueError):
            Protein(namespace="")

        with self.assertRaises(TypeError):
            Protein(namespace="uniprot", name=1234)

        with self.assertRaises(TypeError):
            Protein(namespace="uniprot", identifier=1234)

        with self.assertRaises(ValueError):
            Protein(namespace="uniprot", name="")

        with self.assertRaises(ValueError):
            Protein(namespace="uniprot", identifier="")

        with self.assertRaises(ValueError):
            Protein(namespace="uniprot", identifier="12345", name="")

        with self.assertRaises(ValueError):
            Protein(namespace="uniprot", identifier="", name="123")

    def test_abundance_as_bel_dash_unquoted(self):
        """Test converting an abundance to BEL with a name that needs quotation."""
        namespace, name = "HGNC", "YFG-1"
        node = Abundance(namespace=namespace, name=name)
        self.assertEqual("a(HGNC:YFG-1)", node.as_bel())

    def test_abundance_as_no_quotes(self):
        """Test converting an abundance that doesn't need quotes, but looks crazy."""
        namespace, name = "a-c", "d.e.f"
        node = Abundance(namespace=namespace, name=name)
        self.assertEqual("a(a-c:d.e.f)", node.as_bel())

    def test_abundance_as_bel_quoted(self):
        """Test converting an abundance to BEL with a name that needs quotation."""
        namespace, name = "HGNC", "YFG~1"
        node = Abundance(namespace=namespace, name=name)
        self.assertEqual('a(HGNC:"YFG~1")', node.as_bel())

    def test_abundance_as_bel(self):
        """Test converting an abundance to BEL with a name that does not need quotation."""
        namespace, name = "HGNC", "YFG"
        node = Abundance(namespace=namespace, name=name)
        self.assertEqual("a(HGNC:YFG)", node.as_bel())

    def test_str_has_identifier(self):
        namespace, identifier = n(), n()
        node = Abundance(namespace=namespace, identifier=identifier)
        self.assertEqual(
            "a({namespace}:{identifier})".format(namespace=namespace, identifier=ensure_quotes(identifier)),
            node.as_bel(),
        )

    def test_str_has_both(self):
        namespace, identifier = n(), n()
        node = Abundance(namespace=namespace, identifier=identifier)
        self.assertEqual(
            "a({namespace}:{identifier})".format(namespace=namespace, identifier=ensure_quotes(identifier)),
            node.as_bel(),
        )

    def test_as_tuple(self):
        namespace, name = n(), n()
        node = Abundance(namespace=namespace, name=name)
        self.assertEqual(hash(node), hash(node.as_bel()))

    def test_empty_complex(self):
        """Test that an empty complex causes a failure."""
        with self.assertRaises(ValueError):
            ComplexAbundance(members=[])

    def test_empty_composite(self):
        """Test that an empty complex causes a failure."""
        with self.assertRaises(ValueError):
            CompositeAbundance(members=[])

    def test_complex_with_name(self):
        """Test what happens with a named complex.

        .. code-block::

            complex(SCOMP:"9-1-1 Complex") hasComponent p(HGNC:HUS1)
            complex(SCOMP:"9-1-1 Complex") hasComponent p(HGNC:RAD1)
            complex(SCOMP:"9-1-1 Complex") hasComponent p(HGNC:RAD9A)

        """
        hus1 = Protein(namespace="HGNC", name="HUS1")
        rad1 = Protein(namespace="HGNC", name="RAD1")
        rad9a = Protein(namespace="HGNC", name="RAD9A")
        members = [hus1, rad1, rad9a]

        nine_one_one = ComplexAbundance(members=members, namespace="SCOMP", name="9-1-1 Complex")

        graph = BELGraph()

        graph.add_node_from_data(nine_one_one)
        self.assertIn(nine_one_one, graph)
        self.assertIn(hus1, graph)
        self.assertIn(rad1, graph)
        self.assertIn(rad9a, graph)

    def test_GeneFusion(self):
        """Test serialization of a gene fusion to BEL with a explicit fusion ranges."""
        dsl = GeneFusion(
            Gene("HGNC", "TMPRSS2"),
            Gene("HGNC", "ERG"),
            EnumeratedFusionRange("c", 1, 79),
            EnumeratedFusionRange("c", 312, 5034),
        )
        self.assertEqual('g(fus(HGNC:TMPRSS2, "c.1_79", HGNC:ERG, "c.312_5034"))', dsl.as_bel())

    def test_gene_fusion_missing_implicit(self):
        """Test serialization of a gene fusion to BEL with a implicit missing fusion ranges."""
        dsl = GeneFusion(
            Gene("HGNC", "TMPRSS2"),
            Gene("HGNC", "ERG"),
        )
        self.assertEqual('g(fus(HGNC:TMPRSS2, "?", HGNC:ERG, "?"))', dsl.as_bel())

    def test_gene_fusion_missing_explicit(self):
        """Test serialization of a gene fusion to BEL with an explicit missing fusion ranges."""
        dsl = GeneFusion(
            Gene("HGNC", "TMPRSS2"),
            Gene("HGNC", "ERG"),
            MissingFusionRange(),
            MissingFusionRange(),
        )
        self.assertEqual('g(fus(HGNC:TMPRSS2, "?", HGNC:ERG, "?"))', dsl.as_bel())


class TestCentralDogma(unittest.TestCase):
    """Test functions specific for :class:`CentralDogmaAbundance`s."""

    def test_get_parent(self):
        """Test the get_parent function in :class:`CentralDogmaAbundance`s."""
        ab42 = Protein(name="APP", namespace="HGNC", variants=[Fragment(start=672, stop=713)])
        app = ab42.get_parent()
        self.assertEqual("p(HGNC:APP)", app.as_bel())
        self.assertEqual('p(HGNC:APP, frag("672_713"))', ab42.as_bel())

    def test_with_variants(self):
        """Test the `with_variant` function in :class:`CentralDogmaAbundance`s."""
        app = Protein(name="APP", namespace="HGNC")
        ab42 = app.with_variants(Fragment(start=672, stop=713))
        self.assertEqual("p(HGNC:APP)", app.as_bel())
        self.assertEqual('p(HGNC:APP, frag("672_713"))', ab42.as_bel())

    def test_with_variants_list(self):
        """Test the `with_variant` function in :class:`CentralDogmaAbundance`s."""
        app = Protein(name="APP", namespace="HGNC")
        ab42 = app.with_variants([Fragment(start=672, stop=713)])
        self.assertEqual("p(HGNC:APP)", app.as_bel())
        self.assertEqual('p(HGNC:APP, frag("672_713"))', ab42.as_bel())

    def test_list_abundance_has_contents(self):
        """Test that the construction of list abundance doesn't have empty lists."""
        with self.assertRaises(ListAbundanceEmptyException):
            ComplexAbundance([])

        with self.assertRaises(ListAbundanceEmptyException):
            CompositeAbundance([])

    def test_reaction(self):
        """Add identified reaction."""
        graph = BELGraph()
        reaction = Reaction(
            namespace="rhea",
            identifier="44104",
            reactants=[
                Abundance(namespace="chebi", identifier="17478"),
                Abundance(namespace="chebi", identifier="15377"),
                Abundance(namespace="chebi", identifier="57540"),
            ],
            products=[
                Abundance(namespace="chebi", identifier="29067"),
                Abundance(namespace="chebi", identifier="15378"),
                Abundance(namespace="chebi", identifier="57945"),
            ],
        )
        graph.add_node_from_data(reaction)
        self.assertEqual(7, graph.number_of_nodes())
        self.assertEqual(6, graph.number_of_edges())

    def test_reaction_has_contents(self):
        """Test that the construction of reaction doesn't have empty lists."""
        with self.assertRaises(ReactionEmptyException):
            Reaction([], [])


class TestParse(unittest.TestCase):
    """Test that :func:`parse_result_to_dsl` works correctly."""

    def test_named_complex(self):
        x = ComplexAbundance(
            namespace="a",
            identifier="b",
            members=[
                Protein(namespace="c", identifier="d"),
                Protein(namespace="c", identifier="e"),
            ],
        )

        y = parse_result_to_dsl(dict(x))
        self.assertIsInstance(y, ComplexAbundance)
        self.assertIn(pc.MEMBERS, y)
        self.assertIn(pc.CONCEPT, y)


if __name__ == "__main__":
    unittest.main()
