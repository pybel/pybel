import json
import logging
import unittest

from pybel.constants import *
from pybel.io.jgif import from_jgif, from_cbn_jgif
from tests.constants import bel_dir_path, TestGraphMixin

test_path = os.path.join(bel_dir_path, 'Cytotoxic T-cell Signaling-2.0-Hs.json')

logging.getLogger('pybel.parser').setLevel(20)

jgif_expected_nodes = [
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
    (PROTEIN, 'SFAM', 'Chemokine Receptor Family'),
    (COMPLEX, (PROTEIN, 'HGNC', 'CD8A'), (PROTEIN, 'HGNC', 'CD8B')),
    (COMPLEX, (PROTEIN, 'HGNC', 'CD8A'), (PROTEIN, 'HGNC', 'CD8B')),
    (PROTEIN, 'HGNC', 'PLCG1', (PMOD, (BEL_DEFAULT_NAMESPACE, 'Ph'), 'Tyr')),
    (PROTEIN, 'MGI', 'Il2rg'),
    (COMPLEX, 'SCOMP', 'Calcineurin Complex'),
    (PROTEIN, 'EGID', '21577'),
]

jgif_expected_edges = [

]


class TestJgif(TestGraphMixin):
    """Tests data interchange of """

    def test_import_jgif(self):
        """Tests data from CBN"""
        with open(test_path) as f:
            graph_jgif_dict = json.load(f)

        graph = from_cbn_jgif(graph_jgif_dict)

        self.assertEqual(set(jgif_expected_nodes), set(graph.nodes_iter()))
        self.assertEqual({(u, v) for u, v, d in jgif_expected_edges}, set(graph.edges_iter()))


if __name__ == '__main__':
    unittest.main()
