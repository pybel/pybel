# -*- coding: utf-8 -*-

import unittest

from pybel import BELGraph
from pybel.constants import ANNOTATIONS, INCREASES
from pybel.dsl import protein
from pybel.struct.mutation import strip_annotations


class TestMutations(unittest.TestCase):
    def test_strip_annotations(self):
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


if __name__ == '__main__':
    unittest.main()
