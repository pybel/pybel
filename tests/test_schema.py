# -*- coding: utf-8 -*-

"""Tests for the jsonschema node validation."""

import copy
import json
import os
import unittest

import pybel.dsl
from pybel.schema import is_valid_edge, is_valid_node
from pybel.testing.utils import n

NAMESPACE, NAME, IDENTIFIER = n(), n(), n()

BLANK_ABUNDANCE = {
    "function": "",
    "variants": []
}

# Abundances
PROTEIN = pybel.dsl.Protein(namespace=NAMESPACE, name=NAME, identifier=IDENTIFIER)
GENE = pybel.dsl.Gene(NAMESPACE, name=NAME, identifier=IDENTIFIER)

# Variants
GENE_MOD = pybel.dsl.GeneModification(NAME, namespace=NAMESPACE, identifier=IDENTIFIER)
PROTEIN_SUB = pybel.dsl.ProteinSubstitution('Ala', 1, 'Tyr')
PROTEIN_MOD = pybel.dsl.ProteinModification(NAME, code='Ala', position=1,
                                            namespace=NAMESPACE, identifier=IDENTIFIER)
FRAGMENT = pybel.dsl.Fragment(1, 2)


class TestNodeSchema(unittest.TestCase):
    """Tests for the jsonschema node validation."""

    def test_pure_abundances(self):
        """Test validating abundance nodes."""
        self.assertTrue(is_valid_node(PROTEIN))
        self.assertTrue(is_valid_node(GENE))

        abundance = pybel.dsl.Abundance(namespace=NAMESPACE, name=NAME, identifier=IDENTIFIER)
        self.assertTrue(is_valid_node(abundance))

    def test_variant_abundances(self):
        """Test validating abundance nodes with variants."""
        gmod = GENE.with_variants(GENE_MOD)
        self.assertTrue(is_valid_node(gmod))

        psub = PROTEIN.with_variants(PROTEIN_SUB)
        self.assertTrue(is_valid_node(psub))

        pmod = PROTEIN.with_variants(PROTEIN_MOD)
        self.assertTrue(is_valid_node(pmod))

        frag = PROTEIN.with_variants(FRAGMENT)
        self.assertTrue(is_valid_node(frag))

    def test_matching_variants(self):
        """Test catching invalid abundance/variant pairs, e.g. ProteinModification on a Gene."""
        invalid_gmod = PROTEIN.with_variants(GENE_MOD)
        self.assertFalse(is_valid_node(invalid_gmod))

        invalid_psub = GENE.with_variants(PROTEIN_SUB)
        self.assertFalse(is_valid_node(invalid_psub))

        invalid_pmod = GENE.with_variants(PROTEIN_MOD)
        self.assertFalse(is_valid_node(invalid_pmod))

        invalid_frag = GENE.with_variants(FRAGMENT)
        self.assertFalse(is_valid_node(invalid_frag))

    def test_fusions(self):
        """Test validating fusion nodes."""
        protein = pybel.dsl.Protein(namespace=NAMESPACE, name=NAME,
                                    identifier=IDENTIFIER)
        enum_fusion_range = pybel.dsl.EnumeratedFusionRange("r", 1, 79)
        missing_fusion_range = pybel.dsl.MissingFusionRange()
        fusion_node = pybel.dsl.FusionBase(protein, protein,
                                           range_5p=enum_fusion_range,
                                           range_3p=missing_fusion_range)
        self.assertTrue(is_valid_node(fusion_node))

    def test_list_abundances(self):
        """Test validating list abundance nodes."""
        complex_abundance = pybel.dsl.ComplexAbundance(
            [GENE.with_variants(GENE_MOD), PROTEIN.with_variants(PROTEIN_SUB)],
            namespace=NAMESPACE, name=NAME, identifier=IDENTIFIER)
        composite_abundance = pybel.dsl.CompositeAbundance([PROTEIN, complex_abundance])
        self.assertTrue(is_valid_node(complex_abundance))
        self.assertTrue(is_valid_node(composite_abundance))

    def test_reaction(self):
        """Test validating a reaction node."""
        node = pybel.dsl.Rna(namespace=NAMESPACE, name=NAME, identifier=IDENTIFIER)
        node_list = [node, PROTEIN, GENE]
        rxn = pybel.dsl.Reaction(reactants=node_list, products=node_list)
        self.assertTrue(is_valid_node(rxn))

    def test_invalid_abundances(self):
        """Test that invalid abundances are caught."""
        missing_fn = BLANK_ABUNDANCE.copy()
        missing_fn.pop("function")
        self.assertFalse(is_valid_node(missing_fn))

    def test_invalid_psub(self):
        """Test that invalid protein substitutions are caught."""
        missing_hgvs = dict(PROTEIN_SUB)
        # Remove the required "hgvs" property
        missing_hgvs.pop("hgvs")
        protein = BLANK_ABUNDANCE.copy()
        protein["function"] = "Protein"
        protein["variants"] = [missing_hgvs]
        self.assertFalse(is_valid_node(protein))

    def test_invalid_amino(self):
        """Test that protein variants with invalid amino acid codes are caught."""
        invalid_psub = dict(PROTEIN_SUB)
        invalid_psub['hgvs'] = 'p.Aaa0Bbb'
        self.assertFalse(is_valid_node(invalid_psub))

        invalid_pmod = dict(PROTEIN_MOD)
        invalid_pmod['code'] = 'Aaa'
        self.assertFalse(is_valid_node(invalid_pmod))


class TestEdgeSchema(unittest.TestCase):
    """Tests for the jsonschema edge validation."""

    @classmethod
    def setUpClass(cls):
        """Load the edge contained in example_edge.json."""
        here = os.path.abspath(os.path.dirname(__file__))
        example_file = os.path.join(here, 'example_edge.json')
        with open(example_file) as example_json:
            edge = json.load(example_json)
        cls.example_edge = edge

    def test_predefined_example(self):
        """Test a predefined edge example."""
        edge = self.example_edge
        self.assertTrue(is_valid_edge(edge))

    def test_missing_information(self):
        """Test removing information from the predefined edge."""
        edge = self.example_edge

        missing_source = copy.deepcopy(edge)
        missing_source.pop('source')
        self.assertFalse(is_valid_edge(missing_source))

        missing_relation = copy.deepcopy(edge)
        missing_relation.pop('relation')
        self.assertFalse(is_valid_edge(missing_relation))

        missing_target = copy.deepcopy(edge)
        missing_target.pop('target')
        self.assertFalse(is_valid_edge(missing_target))

        missing_location = copy.deepcopy(edge)
        missing_location['target']['effect'].pop('fromLoc')
        self.assertFalse(is_valid_edge(missing_location))


if __name__ == '__main__':
    unittest.main()
