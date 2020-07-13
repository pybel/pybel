# -*- coding: utf-8 -*-

"""Tests for the repository class."""

import os
import tempfile

from pybel import to_bel_script, to_nodelink_file, to_pickle
from pybel.examples import egf_graph
from pybel.repository import BELRepository
from pybel.testing.cases import TemporaryCacheMixin


class TestRepository(TemporaryCacheMixin):
    """Tests for the repository class."""

    def test_repository(self):
        """Test the repository class."""
        name = 'egf.bel'

        with tempfile.TemporaryDirectory() as temporary_directory:
            bel_path = os.path.join(temporary_directory, name)
            json_path = os.path.join(temporary_directory, f'{name}.json')
            pickle_path = os.path.join(temporary_directory, f'{name}.pickle')
            to_bel_script(egf_graph, bel_path)
            to_nodelink_file(egf_graph, json_path)
            to_pickle(egf_graph, pickle_path)

            repository = BELRepository(temporary_directory)
            graphs = repository.get_graphs(
                manager=self.manager,
                use_cached=True,
                use_tqdm=False,
            )
            self.assertNotEqual(0, len(graphs), msg='No graphs returned')
            self.assertEqual(1, len(graphs))
            self.assertIn(bel_path, graphs)
            graph = graphs[bel_path]
            self.assertEqual(graph.document, egf_graph.document)
            self.assertEqual(set(graph.nodes()), set(egf_graph.nodes()), msg=f"""
            Original nodes: {set(egf_graph.nodes())}
            New nodes:      {set(graph.nodes())}
            """)
            self.assertEqual(set(graph.edges()), set(egf_graph.edges()), msg=f"""
            Original edges: {set(egf_graph.edges())}
            New edges:      {set(graph.edges())}
            """)

            self.assertTrue(os.path.exists(json_path))
            self.assertTrue(os.path.exists(pickle_path))
