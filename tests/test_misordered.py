import unittest

from pybel import from_path
from pybel.constants import *
from tests.constants import bel_dir_path, assertHasEdge, AKT1, EGFR, CASP8, FADD

test_misordered_bel_path = os.path.join(bel_dir_path, 'misordered.bel')

citation = {
    CITATION_TYPE: 'PubMed',
    CITATION_REFERENCE: "123455",
    CITATION_NAME: 'That one article from last week'
}
evidence = 'Evidence 1'
testan1 = '1'


class TestMisordered(unittest.TestCase):
    def test_misordered(self):
        graph = from_path(test_misordered_bel_path, citation_clearing=False)
        self.assertEqual(4, graph.number_of_nodes())
        self.assertEqual(3, graph.number_of_edges())

        e1 = {
            RELATION: INCREASES,
            CITATION: citation,
            EVIDENCE: evidence,
            ANNOTATIONS: {
                'TESTAN1': testan1
            }
        }
        assertHasEdge(self, AKT1, EGFR, graph, **e1)

        e2 = {
            RELATION: DECREASES,
            CITATION: citation,
            EVIDENCE: evidence,
            ANNOTATIONS: {
                'TESTAN1': testan1
            }
        }
        assertHasEdge(self, EGFR, FADD, graph, **e2)

        e3 = {
            RELATION: DIRECTLY_DECREASES,
            CITATION: citation,
            EVIDENCE: evidence,
            ANNOTATIONS: {
                'TESTAN1': testan1
            }
        }
        assertHasEdge(self, EGFR, CASP8, graph, **e3)
