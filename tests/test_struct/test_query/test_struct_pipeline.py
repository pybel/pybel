# -*- coding: utf-8 -*-

import logging
import unittest
from io import StringIO

from pybel import BELGraph
from pybel.examples.egf_example import egf_graph
from pybel.struct.mutation import enrich_protein_and_rna_origins
from pybel.struct.pipeline import Pipeline
from pybel.struct.pipeline.decorators import get_transformation, mapped
from pybel.struct.pipeline.exc import MetaValueError, MissingPipelineFunctionError

log = logging.getLogger(__name__)
log.setLevel(10)


class TestEgfExample(unittest.TestCase):
    """Random test for mutation functions"""

    def setUp(self):
        self.graph = egf_graph.copy()
        self.original_number_nodes = self.graph.number_of_nodes()
        self.original_number_edges = self.graph.number_of_edges()

    def check_original_unchanged(self):
        self.assertEqual(self.original_number_nodes, self.graph.number_of_nodes(),
                         msg='original graph nodes should remain unchanged')
        self.assertEqual(self.original_number_edges, self.graph.number_of_edges(),
                         msg='original graph edges should remain unchanged')


class TestPipelineFailures(unittest.TestCase):

    def test_assert_failure(self):
        with self.assertRaises(MissingPipelineFunctionError):
            get_transformation('missing function')

    def test_assert_success(self):
        m = list(mapped)
        self.assertLess(0, len(m))
        m = m[0]
        f = get_transformation(m)
        self.assertIsNotNone(f)

    def test_append_invalid(self):
        """Test when an invalid type is given to a :class:`pybel.struct.Pipeline`."""
        p = Pipeline()
        with self.assertRaises(TypeError):
            p.append(4)

    def test_get_function_failure(self):
        p = Pipeline()

        with self.assertRaises(MissingPipelineFunctionError):
            p._get_function('nonsense name')

    def test_build_meta_failure(self):
        p1, p2 = Pipeline(), Pipeline()

        p = Pipeline._build_meta('wrong', [p1, p2])

        with self.assertRaises(MetaValueError):
            p(BELGraph())

    def test_fail_add(self):
        pipeline = Pipeline()
        with self.assertRaises(MissingPipelineFunctionError):
            pipeline.append('missing function')


class TestPipeline(TestEgfExample):
    def test_append(self):
        pipeline = Pipeline()
        self.assertEqual(0, len(pipeline))

        pipeline.append('enrich_protein_and_rna_origins')
        self.assertEqual(1, len(pipeline))

    def test_extend(self):
        p1 = Pipeline.from_functions(['enrich_protein_and_rna_origins'])
        self.assertEqual(1, len(p1))

        p2 = Pipeline.from_functions(['remove_pathologies'])
        p1.extend(p2)

        self.assertEqual(2, len(p1))

    def test_serialize_string(self):
        p = Pipeline.from_functions(['enrich_protein_and_rna_origins'])
        s = p.dumps()
        p_reconstituted = Pipeline.loads(s)
        self.assertEqual(p.protocol, p_reconstituted.protocol)

    def test_serialize_file(self):
        p = Pipeline.from_functions(['enrich_protein_and_rna_origins'])
        sio = StringIO()
        p.dump(sio)
        sio.seek(0)
        p_reconstituted = Pipeline.load(sio)
        self.assertEqual(p.protocol, p_reconstituted.protocol)

    def test_pipeline_by_string(self):
        pipeline = Pipeline.from_functions([
            'enrich_protein_and_rna_origins',
        ])
        result = pipeline(self.graph)

        self.assertEqual(32, result.number_of_nodes())

        for node in self.graph:
            self.assertIn(node, result)

        self.check_original_unchanged()

    def test_pipeline_by_function(self):
        pipeline = Pipeline.from_functions([
            enrich_protein_and_rna_origins,
        ])
        result = pipeline(self.graph)

        self.assertEqual(32, result.number_of_nodes())

        for node in self.graph:
            self.assertIn(node, result)

        self.check_original_unchanged()
