# -*- coding: utf-8 -*-

"""Tests for metadata transforations."""

import unittest

from pybel import BELGraph
from pybel.constants import (
    ANNOTATIONS, CITATION, CITATION_AUTHORS, CITATION_DATE, CITATION_REFERENCE, CITATION_TYPE, CITATION_TYPE_PUBMED,
)
from pybel.dsl import protein
from pybel.examples import sialic_acid_graph
from pybel.struct.mutation import (
    add_annotation_value, remove_annotation_value, remove_citation_metadata, strip_annotations,
)
from pybel.testing.utils import n


class TestMetadata(unittest.TestCase):
    """Test metadata transformations."""

    def test_strip_annotations(self):
        """Test the strip_annotation function."""
        x = protein(namespace='HGNC', name='X')
        y = protein(namespace='HGNC', name='X')

        graph = BELGraph()
        key = graph.add_increases(
            x,
            y,
            citation='123456',
            evidence='Fake',
            annotations={
                'A': {'B': True}
            },
        )

        self.assertIn(ANNOTATIONS, graph[x][y][key])

        strip_annotations(graph)
        self.assertNotIn(ANNOTATIONS, graph[x][y][key])

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

    def test_remove_citation_metadata(self):
        """Test removing citation metadata from a graph."""
        x = protein(namespace='HGNC', name='X')
        y = protein(namespace='HGNC', name='X')

        graph = BELGraph()

        k0 = graph.add_part_of(x, y)
        k1 = graph.add_increases(
            x,
            y,
            citation='123456',
            evidence='Fake',
            annotations={
                'A': {'B': True}
            },
        )
        k2 = graph.add_increases(
            x,
            y,
            citation={
                CITATION_TYPE: CITATION_TYPE_PUBMED,
                CITATION_REFERENCE: '12345678',
                CITATION_DATE: '2018-12-10',
            },
            evidence='Fake',
            annotations={
                'A': {'B': True}
            },
        )

        remove_citation_metadata(graph)

        self.assertNotIn(CITATION, graph[x][y][k0])

        for k in k1, k2:
            self.assertIn(CITATION, graph[x][y][k])
            self.assertIn(CITATION_TYPE, graph[x][y][k][CITATION])
            self.assertIn(CITATION_REFERENCE, graph[x][y][k][CITATION])
            self.assertNotIn(CITATION_DATE, graph[x][y][k][CITATION])
            self.assertNotIn(CITATION_AUTHORS, graph[x][y][k][CITATION])
