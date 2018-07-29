# -*- coding: utf-8 -*-

"""Tests for metadata transforations."""

import unittest

from pybel import BELGraph
from pybel.constants import ANNOTATIONS, INCREASES
from pybel.dsl import protein
from pybel.examples import sialic_acid_graph
from pybel.struct.mutation import add_annotation_value, remove_annotation_value, strip_annotations
from pybel.testing.utils import n


class TestMetadata(unittest.TestCase):
    """Test metadata transformations."""

    def test_strip_annotations(self):
        """Test the strip_annotation function."""
        x = protein(namespace='HGNC', name='X')
        y = protein(namespace='HGNC', name='X')

        graph = BELGraph()
        graph.add_qualified_edge(
            x,
            y,
            relation=INCREASES,
            citation='123456',
            evidence='Fake',
            annotations={
                'A': {'B': True}
            },
            key=1
        )

        self.assertIn(ANNOTATIONS, graph.edge[x.as_tuple()][y.as_tuple()][1])

        strip_annotations(graph)
        self.assertNotIn(ANNOTATIONS, graph.edge[x.as_tuple()][y.as_tuple()][1])

    def test_add_and_remove_annotation(self):
        """Test adding and removing annotations.

        See: :func:`pybel.struct.mutation.add_annotation_value` and
        :func:`pybel.struct.mutation.remove_annotation_value` functions.
        """
        graph = sialic_acid_graph.copy()
        annotation = 'test-annotation'
        value = 'test-value'
        url = n()

        graph.annotation_url[annotation] = url

        add_annotation_value(graph, annotation, value)

        for u, v, d in graph.edges(data=True):
            annotations = d.get(ANNOTATIONS)

            if annotations is None:
                continue

            self.assertIn(annotation, annotations)
            self.assertIn(value, annotations[annotation])

        remove_annotation_value(graph, annotation, value)

        for u, v, d in graph.edges(data=True):
            annotations = d.get(ANNOTATIONS)

            if annotations is None:
                continue

            annotation_values = annotations.get(annotation)

            if annotation_values is None:
                continue

            self.assertNotIn(value, annotation_values)
