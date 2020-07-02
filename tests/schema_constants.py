# -*- coding: utf-8 -*-

"""Constants for PyBEL schema tests."""

import pybel
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
