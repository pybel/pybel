import json
import unittest

from pybel.constants import *
from pybel.io.jgif import from_jgif
from tests.constants import bel_dir_path, assertHasNode
import logging
test_path = os.path.join(bel_dir_path, 'Cytotoxic T-cell Signaling-2.0-Hs.json')

logging.getLogger('pybel.parser').setLevel(20)

class TestJgif(unittest.TestCase):
    def test_1(self):
        """Tests data from CBN"""
        with open(test_path) as f:
            graph_jgif_dict = json.load(f)

        graph = from_jgif(graph_jgif_dict)

        expected_nodes = [
            (PROTEIN, 'HGNC', 'CXCR6'),
            (PROTEIN, 'HGNC', 'IL15RA'),
            (BIOPROCESS, 'GOBP', 'lymphocyte chemotaxis'),
            (PROTEIN, 'HGNC', 'IL2RG'),
            (PROTEIN, 'HGNC', 'ZAP70'),
            (ABUNDANCE, 'SCHEM', 'Calcium'),
            (COMPLEX, 'SCOMP', 'T Cell Receptor Complex'),
            (BIOPROCESS, 'GOBP', 'T cell activation'),
            (PROTEIN, 'HGNC', 'CCL3'),
            (PROTEIN, 'HGNC', 'PLCG1'),
            (PROTEIN, 'HGNC', 'FASLG'),
            (PROTEIN, 'HGNC', 'IDO1'),
            (PROTEIN, 'HGNC', 'IL2'),
            (PROTEIN, 'HGNC', 'CD8A'),
            (PROTEIN, 'HGNC', 'CD8B'),
            (PROTEIN, 'HGNC', 'PLCG1'),
            (PROTEIN, 'HGNC', 'BCL2'),
            (PROTEIN, 'HGNC', 'CCR3'),
            (PROTEIN, 'HGNC', 'IL15'),
            (PROTEIN, 'HGNC', 'IL2RB'),
            (PROTEIN, 'HGNC', 'CD28'),
            (PATHOLOGY, 'SDIS', 'Cytotoxic T-cell activation'),
            (PROTEIN, 'HGNC', 'FYN'),
            (PROTEIN, 'HGNC', 'CXCL16'),
            (PROTEIN, 'HGNC', 'CCR5'),
            (PROTEIN, 'HGNC', 'LCK'),
            (PROTEIN, 'SFAM', 'Chemokine Receptor Family'),
            (PROTEIN, 'HGNC', 'CXCL9'),
            (PATHOLOGY, 'SDIS', 'T-cell migration'),
            (PROTEIN, 'HGNC', 'CXCR3'),
            (PROTEIN, 'HGNC', 'FOXO3'),
            (BIOPROCESS, 'GOBP', 'CD8-positive, alpha-beta T cell proliferation'),
            (ABUNDANCE, 'CHEBI', 'acrolein'),
            (PROTEIN, 'HGNC', 'IDO2'),
            (PATHOLOGY, 'MESHD', 'Pulmonary Disease, Chronic Obstructive'),
            (PROTEIN, 'HGNC', 'IFNG'),
            (PROTEIN, 'HGNC', 'TNFRSF4'),
            (PROTEIN, 'HGNC', 'CTLA4'),
            (PROTEIN, 'HGNC', 'GZMA'),
            (PROTEIN, 'HGNC', 'PRF1'),
            (PROTEIN, 'HGNC', 'TNF'),
            ('Protein', 'SFAM', 'Chemokine Receptor Family')
        ]

        #for node in expected_nodes:
        #   assertHasNode(self, node, graph)
        self.assertEqual(set(expected_nodes), set(graph.nodes_iter()))

if __name__ == '__main__':
    unittest.main()
