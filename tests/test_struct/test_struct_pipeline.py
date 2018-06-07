# -*- coding: utf-8 -*-

import logging
import unittest

from pybel.examples.egf_example import egf_graph
from pybel.struct.mutation import infer_central_dogma
from pybel.struct.pipeline import Pipeline
from pybel.struct.pipeline.decorators import get_transformation, mapped
from pybel.struct.pipeline.exc import MissingPipelineFunctionError

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
        pass

    def test_get_function_success(self):
        pass

    def test_fail_add(self):
        pipeline = Pipeline()
        with self.assertRaises(MissingPipelineFunctionError):
            pipeline.append('missing function')

    def test_fail_build(self):
        protocol = [{'function': 'missing function'}]
        with self.assertRaises(MissingPipelineFunctionError):
            Pipeline(protocol=protocol)

    def test_fail_from_json(self):
        protocol = [{'function': 'missing function'}]
        with self.assertRaises(MissingPipelineFunctionError):
            Pipeline.from_json(protocol)


class TestPipeline(TestEgfExample):
    def test_central_dogma_is_registered(self):
        self.assertIn('infer_central_dogma', mapped)

    def test_append(self):
        pipeline = Pipeline()
        self.assertEqual(0, len(pipeline))

        pipeline.append('infer_central_dogma')
        self.assertEqual(1, len(pipeline))

    def test_extend(self):
        p1 = Pipeline.from_functions(['infer_central_dogma'])
        p2 = Pipeline.from_functions(['remove_pathologies'])
        p1.extend(p2)

    def test_pipeline_by_string(self):
        pipeline = Pipeline.from_functions([
            'infer_central_dogma',
        ])
        result = pipeline.run(self.graph, in_place=False)

        self.assertEqual(32, result.number_of_nodes())

        for node in self.graph:
            self.assertIn(node, result)

        self.check_original_unchanged()

    def test_pipeline_by_function(self):
        pipeline = Pipeline.from_functions([
            infer_central_dogma,
        ])
        result = pipeline.run(self.graph, in_place=False)

        self.assertEqual(32, result.number_of_nodes())

        for node in self.graph:
            self.assertIn(node, result)

        self.check_original_unchanged()
