# -*- coding: utf-8 -*-

"""Test the user API."""

import unittest

import pybel


class TestParse(unittest.TestCase):
    """Test user API."""

    def test_bel_statement(self):
        for bel in [
            'p(hgnc:1234) -> p(hgnc:1235)',
            'p(hgnc:1234) hasVariant p(hgnc:1234, pmod(Ph))',
            'p(hgnc:1) => rxn(reactants(a(chebi:1), a(chebi:2)), products(a(chebi:3), a(chebi:4)))',
            'r(hgnc:1) pos r(hgnc:2)',
            'r(hgnc:1) cor r(hgnc:2)',
            'r(hgnc:1) eq r(ncbigene:5)',
            'p(hgnc:1) -> (p(hgnc:2) -> p(hgnc:3))',
            'p(hgnc:1)',
        ]:
            with self.subTest(bel=bel):
                x = pybel.parse(bel)

    def test_citation(self):
        x = pybel.parse('SET Citation = pmid:1234')

    def test_control(self):
        x = pybel.parse('SET Test = "5"')

    def test_control_multiple(self):
        x = pybel.parse('SET Test = {"1","2","3"}')
