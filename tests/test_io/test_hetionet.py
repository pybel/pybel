# -*- coding: utf-8 -*-

"""Importer for Hetionet JSON."""

import unittest

from pybel import dsl
from pybel.io.hetionet import ANATOMY, GENE, from_hetionet_dict


class TestHetionet(unittest.TestCase):
    """"""

    def test_import(self):
        """"""
        self._help(
            h_type=ANATOMY,
            h_dsl=dsl.Population,
            h_namespace='uberon',
            h_id='UBERON:1',
            h_name='anatomy1',
            kind='upregulates',
            t_type=GENE,
            t_dsl=dsl.Rna,
            t_namespace='ncbigene',
            t_id='1',
            t_name='gene1',
        )

    def _help(
        self,
        h_type, h_dsl, h_namespace, h_id, h_name,
        kind,
        t_type, t_dsl, t_namespace, t_id, t_name,
    ):
        source = dict(kind=h_type, identifier=h_id, name=h_name)
        target = dict(kind=t_type, identifier=t_id, name=t_name)
        edge = dict(
            source_id=(h_type, h_id),
            kind=kind,
            target_id=(t_type, t_id),
            data={},
        )

        graph = from_hetionet_dict(dict(nodes=[source, target], edges=[edge]))
        source_node = h_dsl(namespace=h_namespace, identifier=h_id, name=h_name)
        self.assertIn(source_node, graph, msg='Nodes: {}'.format(list(graph)))
        target_node = t_dsl(namespace=t_namespace, identifier=t_id, name=t_name)
        self.assertIn(target_node, graph, msg='Nodes: {}'.format(list(graph)))
        self.assertEqual(2, graph.number_of_nodes())

        self.assertIn(target_node, graph[source_node])
