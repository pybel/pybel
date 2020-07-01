# -*- coding: utf-8 -*-

"""Tests for the jsonschema node validation."""

import unittest

from pybel.schema import is_valid_node
import pybel.dsl
from pybel.testing.utils import n


VALID_ENTITY = {
    "namespace": "",
    "name": "",
    "identifier": ""
}

VALID_VARIANT = {
    "kind": "",
    "concept": VALID_ENTITY,
    "code": "",
    "pos": 0
}

VALID_ABUNDANCE = {
    "function": "",
    "concept": VALID_ENTITY,
    "xrefs": [VALID_ENTITY, VALID_ENTITY],
    "variants": [VALID_VARIANT, VALID_VARIANT]
}

NAMESPACE, NAME, IDENTIFIER = n(), n(), n()

def build_abundance(variant_dict):
    """Return an abundance dict with the given variant."""
    abundance = VALID_ABUNDANCE.copy()
    abundance["variants"] = [variant_dict, variant_dict]
    return abundance


class TestSchema(unittest.TestCase):
    """Tests for the jsonschema node validation."""

    def test_pure_abundances(self):
        """Test validating abundance nodes."""
        abundance = pybel.dsl.Abundance(namespace=NAMESPACE, name=NAME, identifier=IDENTIFIER)
        protein = pybel.dsl.Protein(namespace=NAMESPACE, name=NAME,
                                    identifier=IDENTIFIER)
        self.assertTrue(is_valid_node(abundance))
        self.assertTrue(is_valid_node(protein))

    def test_variant_abundances(self):
        """Test validating abundance nodes with variants."""
        gene_mod = pybel.dsl.GeneModification(NAME, namespace=NAMESPACE, identifier=IDENTIFIER)
        protein_sub = pybel.dsl.ProteinSubstitution('Abc', 1, 'Def')
        protein_mod = pybel.dsl.ProteinModification(NAME, code='Abc', position=1,
                                                    namespace=NAMESPACE, identifier=IDENTIFIER)
        fragment = pybel.dsl.Fragment(1, 2)
        node = lambda variant: pybel.dsl.Gene(NAMESPACE, name=NAME,
                                              identifier=IDENTIFIER, variants=[variant])
        self.assertTrue(is_valid_node(node(protein_mod)))
        self.assertTrue(is_valid_node(node(gene_mod)))
        self.assertTrue(is_valid_node(node(protein_sub)))
        self.assertTrue(is_valid_node(node(fragment)))

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
        node = pybel.dsl.Gene(namespace=NAMESPACE, name=NAME, identifier=IDENTIFIER)
        complex_abundance = pybel.dsl.ComplexAbundance([node, node], namespace=NAMESPACE,
                                                       name=NAME, identifier=IDENTIFIER)
        composite_abundance = pybel.dsl.CompositeAbundance([node, complex_abundance])
        self.assertTrue(is_valid_node(complex_abundance))
        self.assertTrue(is_valid_node(composite_abundance))

    def test_reaction(self):
        """Test validating a reaction node."""
        node = pybel.dsl.Rna(namespace=NAMESPACE, name=NAME, identifier=IDENTIFIER)
        node_list = [node, node, node]
        rxn = pybel.dsl.Reaction(reactants=node_list, products=node_list)
        self.assertTrue(is_valid_node(rxn))

    def test_invalid_abundances(self):
        """Test that invalid abundances are caught."""
        missing_fn = VALID_ABUNDANCE.copy()
        missing_fn.pop("function")
        self.assertFalse(is_valid_node(missing_fn))

    def test_invalid_pmod(self):
        """Test that invalid protein modifications are caught."""
        protein_mod = pybel.dsl.ProteinModification(NAME, code='Abc', position=1,
                                                    namespace=NAMESPACE, identifier=IDENTIFIER)
        protein_mod = dict(protein_mod)
        # Remove the required "code" property
        missing_code = protein_mod.copy()
        missing_code.pop("code")
        node = build_abundance(missing_code)
        self.assertFalse(is_valid_node(node))
        # Remove the required "pos" property
        missing_pos = protein_mod.copy()
        missing_pos.pop("pos")
        node = build_abundance(missing_pos)
        self.assertFalse(is_valid_node(node))

    def test_invalid_frag(self):
        """Test that invalid fragments are caught."""
        fragment = dict(pybel.dsl.Fragment(1, 2))
        # Remove the required "start" property
        missing_start = fragment.copy()
        missing_start.pop("start")
        node = build_abundance(missing_start)
        self.assertFalse(is_valid_node(node))
        # Remove the required "stop" property
        missing_stop = fragment.copy()
        missing_stop.pop("stop")
        node = build_abundance(missing_stop)
        self.assertFalse(is_valid_node(node))

    def test_invalid_psub(self):
        """Test that invalid protein substitutions are caught."""
        protein_sub = dict(pybel.dsl.ProteinSubstitution('Abc', 1, 'Def'))
        # Remove the required "hgvs" property
        protein_sub.pop("hgvs")
        node = build_abundance(protein_sub)
        self.assertFalse(is_valid_node(node))


if __name__ == '__main__':
    unittest.main()
