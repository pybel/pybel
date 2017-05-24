# -*- coding: utf-8 -*-

import unittest

from pybel import from_path
from pybel.constants import *
from tests.constants import FleetingTemporaryCacheMixin, TestGraphMixin
from tests.constants import bel_dir_path, AKT1, EGFR, CASP8, FADD, citation_1

test_misordered_bel_path = os.path.join(bel_dir_path, 'misordered.bel')

evidence = 'Evidence 1'
testan1 = '1'


class TestMisordered(FleetingTemporaryCacheMixin, TestGraphMixin):
    def test_misordered(self):
        """This test ensures that non-citation clearing mode works"""
        graph = from_path(test_misordered_bel_path, manager=self.manager, citation_clearing=False)
        self.assertEqual(4, graph.number_of_nodes())
        self.assertEqual(3, graph.number_of_edges())

        e1 = {
            RELATION: INCREASES,
            CITATION: citation_1,
            EVIDENCE: evidence,
            ANNOTATIONS: {
                'TESTAN1': testan1
            }
        }
        self.assertHasEdge(graph, AKT1, EGFR, **e1)

        e2 = {
            RELATION: DECREASES,
            CITATION: citation_1,
            EVIDENCE: evidence,
            ANNOTATIONS: {
                'TESTAN1': testan1
            }
        }
        self.assertHasEdge(graph, EGFR, FADD, **e2)

        e3 = {
            RELATION: DIRECTLY_DECREASES,
            CITATION: citation_1,
            EVIDENCE: evidence,
            ANNOTATIONS: {
                'TESTAN1': testan1
            }
        }
        self.assertHasEdge(graph, EGFR, CASP8, **e3)


if __name__ == '__main__':
    unittest.main()
