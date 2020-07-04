# -*- coding: utf-8 -*-

"""Test the user API."""

import unittest

import pybel


class TestParse(unittest.TestCase):
    """Test user API."""

    def test_bel_statement(self):
        x = pybel.parse('p(hgnc:1234) -> p(hgnc:1235)')

    def test_citation(self):
        x = pybel.parse('SET Citation = pmid:1234')

    def test_control(self):
        x = pybel.parse('SET Test = "5"')

    def test_control_multiple(self):
        x = pybel.parse('SET Test = {"1","2","3"}')
