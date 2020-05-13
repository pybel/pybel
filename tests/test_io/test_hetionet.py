# -*- coding: utf-8 -*-

"""Importer for Hetionet JSON."""

import unittest

import pybel.io.hetionet.constants as hioc
from pybel import dsl
from pybel.io.hetionet import from_hetionet_json


class TestHetionet(unittest.TestCase):
    def test_import(self):
        self._help(
            h_type=hioc.ANATOMY,
            h_dsl=dsl.Population,
            h_namespace='uberon',
            h_id='UBERON:1',
            h_name='anatomy1',
            kind='upregulates',
            t_type=hioc.GENE,
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

        if h_id.lower().startswith('{}:'.format(h_namespace.lower())):
            h_id = h_id[len(h_namespace) + 1:]

        if t_id.lower().startswith('{}:'.format(t_namespace.lower())):
            t_id = t_id[len(t_namespace) + 1:]

        graph = from_hetionet_json(dict(nodes=[source, target], edges=[edge]), use_tqdm=False)
        source_node = h_dsl(namespace=h_namespace, identifier=h_id, name=h_name)
        self.assertIn(source_node, graph, msg='Nodes: {}'.format(list(graph)))
        target_node = t_dsl(namespace=t_namespace, identifier=t_id, name=t_name)
        self.assertIn(target_node, graph, msg='Nodes: {}'.format(list(graph)))
        self.assertEqual(2, graph.number_of_nodes())

        self.assertIn(target_node, graph[source_node])
