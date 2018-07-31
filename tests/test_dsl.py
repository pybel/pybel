# -*- coding: utf-8 -*-

"""Tests for the internal DSL."""

import unittest

from pybel import BELGraph
from pybel.constants import ABUNDANCE, COMPLEX, FUNCTION, IDENTIFIER, NAME, NAMESPACE, PROTEIN
from pybel.dsl import abundance, complex_abundance, entity, fragment, protein
from pybel.testing.utils import n
from pybel.utils import ensure_quotes, hash_node


class TestDSL(unittest.TestCase):
    """Tests for the internal DSL."""

    def test_add_robust_node(self):
        """Test adding a node with both a name and identifier."""
        graph = BELGraph()
        namespace, name, identifier = n(), n(), n()
        node = protein(namespace=namespace, name=name, identifier=identifier)

        graph.add_node_from_data(node)

        self.assertEqual(
            {
                FUNCTION: PROTEIN,
                NAMESPACE: namespace,
                NAME: name,
                IDENTIFIER: identifier,
            },
            graph.node[node.as_tuple()]
        )

    def test_add_identified_node(self):
        """Test what happens when a node with only an identifier is added to a graph."""
        graph = BELGraph()
        namespace, identifier = n(), n()
        node = protein(namespace=namespace, identifier=identifier)
        self.assertNotIn(NAME, node)

        t = graph.add_node_from_data(node)

        self.assertEqual(
            {
                FUNCTION: PROTEIN,
                NAMESPACE: namespace,
                IDENTIFIER: identifier,
            },
            graph.node[t]
        )

    def test_add_named_node(self):
        graph = BELGraph()
        namespace, name = n(), n()
        node = protein(namespace=namespace, name=name)

        graph.add_node_from_data(node)

        self.assertEqual(
            {
                FUNCTION: PROTEIN,
                NAMESPACE: namespace,
                NAME: name,
            },
            graph.node[node.as_tuple()]
        )

    def test_missing_information(self):
        """Check that entity and abundance functions raise on missing name/identifier."""
        with self.assertRaises(ValueError):
            entity(namespace='test')

        with self.assertRaises(ValueError):
            protein(namespace='test')

    def test_str_has_name(self):
        namespace, name = n(), n()
        node = abundance(namespace=namespace, name=name)
        self.assertEqual('a({namespace}:{name})'.format(namespace=namespace, name=ensure_quotes(name)), node.as_bel())

    def test_str_has_identifier(self):
        namespace, identifier = n(), n()
        node = abundance(namespace=namespace, identifier=identifier)
        self.assertEqual(
            'a({namespace}:{identifier})'.format(namespace=namespace, identifier=ensure_quotes(identifier)),
            node.as_bel())

    def test_str_has_both(self):
        namespace, identifier = n(), n()
        node = abundance(namespace=namespace, identifier=identifier)
        self.assertEqual(
            'a({namespace}:{identifier})'.format(namespace=namespace, identifier=ensure_quotes(identifier)),
            node.as_bel())

    def test_as_tuple(self):
        namespace, name = n(), n()

        node_tuple = ABUNDANCE, namespace, name
        node = abundance(namespace=namespace, name=name)

        self.assertEqual(node_tuple, node.as_tuple())
        self.assertEqual(hash(node_tuple), hash(node))
        self.assertEqual(hash_node(node_tuple), node.as_sha512())

    def test_complex_with_name(self):
        """Tests a what happens with a named complex

        .. code-block::

            complex(SCOMP:"9-1-1 Complex") hasComponent p(HGNC:HUS1)
            complex(SCOMP:"9-1-1 Complex") hasComponent p(HGNC:RAD1)
            complex(SCOMP:"9-1-1 Complex") hasComponent p(HGNC:RAD9A)

        """
        hus1 = protein(namespace='HGNC', name='HUS1')
        rad1 = protein(namespace='HGNC', name='RAD1')
        rad9a = protein(namespace='HGNC', name='RAD9A')
        members = [hus1, rad1, rad9a]

        nine_one_one = complex_abundance(members=members, namespace='SCOMP', name='9-1-1 Complex')

        node_tuple = (COMPLEX,) + tuple(member.as_tuple() for member in members)

        self.assertEqual(node_tuple, nine_one_one.as_tuple())
        self.assertEqual(hash(node_tuple), hash(nine_one_one))
        self.assertEqual(hash_node(node_tuple), nine_one_one.as_sha512())


class TestCentralDogma(unittest.TestCase):
    """Test functions specific for :class:`CentralDogmaAbundance`s."""

    def test_get_parent(self):
        """Test the get_parent function in :class:`CentralDogmaAbundance`s."""
        ab42 = protein(name='APP', namespace='HGNC', variants=[fragment(start=672, stop=713)])
        app = ab42.get_parent()
        self.assertEqual('p(HGNC:APP)', app.as_bel())
        self.assertEqual('p(HGNC:APP, frag(672_713))', ab42.as_bel())

    def test_with_variants(self):
        """Test the `with_variant` function in :class:`CentralDogmaAbundance`s."""
        app = protein(name='APP', namespace='HGNC')
        ab42 = app.with_variants(fragment(start=672, stop=713))
        self.assertEqual('p(HGNC:APP)', app.as_bel())
        self.assertEqual('p(HGNC:APP, frag(672_713))', ab42.as_bel())

    def test_with_variants_list(self):
        """Test the `with_variant` function in :class:`CentralDogmaAbundance`s."""
        app = protein(name='APP', namespace='HGNC')
        ab42 = app.with_variants([fragment(start=672, stop=713)])
        self.assertEqual('p(HGNC:APP)', app.as_bel())
        self.assertEqual('p(HGNC:APP, frag(672_713))', ab42.as_bel())


if __name__ == '__main__':
    unittest.main()
