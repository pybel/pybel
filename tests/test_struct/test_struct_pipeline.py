# -*- coding: utf-8 -*-

import logging
import unittest

from six.moves import StringIO

from pybel import BELGraph
from pybel.examples.egf_example import egf_graph
from pybel.struct.mutation import enrich_protein_and_rna_origins
from pybel.struct.pipeline import Pipeline, transformation
from pybel.struct.pipeline.decorators import (
    deprecated, get_transformation, in_place_map, mapped, register_deprecated,
    universe_map,
)
from pybel.struct.pipeline.exc import DeprecationMappingError, MetaValueError, MissingPipelineFunctionError

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
    def test_deprecated_central_dogma_is_registered(self):
        """Tests that a deprecated function is properly registered"""
        self.assertIn('enrich_protein_and_rna_origins', mapped)
        self.assertIn('infer_central_dogma', mapped)
        self.assertEqual(mapped['enrich_protein_and_rna_origins'], mapped['infer_central_dogma'])

    def test_append(self):
        pipeline = Pipeline()
        self.assertEqual(0, len(pipeline))

        pipeline.append('infer_central_dogma')
        self.assertEqual(1, len(pipeline))

    def test_extend(self):
        p1 = Pipeline.from_functions(['infer_central_dogma'])
        self.assertEqual(1, len(p1))

        p2 = Pipeline.from_functions(['remove_pathologies'])
        p1.extend(p2)

        self.assertEqual(2, len(p1))

    def test_serialize_string(self):
        p = Pipeline.from_functions(['infer_central_dogma'])
        s = p.dumps()
        p_reconstituted = Pipeline.loads(s)
        self.assertEqual(p.protocol, p_reconstituted.protocol)

    def test_serialize_file(self):
        p = Pipeline.from_functions(['infer_central_dogma'])
        sio = StringIO()
        p.dump(sio)
        sio.seek(0)
        p_reconstituted = Pipeline.load(sio)
        self.assertEqual(p.protocol, p_reconstituted.protocol)

    def test_pipeline_by_string(self):
        pipeline = Pipeline.from_functions([
            'infer_central_dogma',
        ])
        result = pipeline(self.graph, in_place=False)

        self.assertEqual(32, result.number_of_nodes())

        for node in self.graph:
            self.assertIn(node, result)

        self.check_original_unchanged()

    def test_pipeline_by_function(self):
        pipeline = Pipeline.from_functions([
            enrich_protein_and_rna_origins,
        ])
        result = pipeline(self.graph, in_place=False)

        self.assertEqual(32, result.number_of_nodes())

        for node in self.graph:
            self.assertIn(node, result)

        self.check_original_unchanged()


class TestDeprecation(unittest.TestCase):

    def test_register_deprecation_remapping_error(self):
        """Test that a deprecation mapping doesn't override a pre-existing mapping."""

        @transformation
        def test_function_1():
            pass

        self.assertNotIn('test_function_1', deprecated)
        self.assertIn('test_function_1', mapped)
        self.assertNotIn('test_function_1', universe_map)
        self.assertNotIn('test_function_1', in_place_map)

        with self.assertRaises(DeprecationMappingError):
            @register_deprecated('test_function_1')
            @transformation
            def test_function_1_new():
                pass

        self.assertNotIn('test_function_1', deprecated)

    def test_register_deprecated(self):
        """Test that a deprecation mapping doesn't override a pre-existing mapping."""

        @register_deprecated('test_function_2_old')
        @transformation
        def test_function_2():
            pass

        self.assertNotIn('test_function_2', deprecated)
        self.assertIn('test_function_2', mapped)
        self.assertNotIn('test_function_2', universe_map)
        self.assertNotIn('test_function_2', in_place_map)

        self.assertIn('test_function_2_old', deprecated)
        self.assertIn('test_function_2_old', mapped)
        self.assertNotIn('test_function_2_old', universe_map)
        self.assertNotIn('test_function_2_old', in_place_map)

        self.assertEqual(mapped['test_function_2_old'], mapped['test_function_2'])

    def test_register_missing(self):
        """Test that a deprecation mapping fails if it's missing a transformation function."""
        with self.assertRaises(MissingPipelineFunctionError):
            @register_deprecated('test_function_3_old')
            def test_function_3():
                pass

        self.assertNotIn('test_function_3', mapped)
        self.assertNotIn('test_function_3', universe_map)
        self.assertNotIn('test_function_3', in_place_map)

        self.assertNotIn('test_function_3_old', deprecated)
        self.assertNotIn('test_function_3_old', mapped)
        self.assertNotIn('test_function_3_old', universe_map)
        self.assertNotIn('test_function_3_old', in_place_map)
