import os
import unittest

from pybel.manager.mapper import MapperManager
from tests.constants import test_eq_1, test_eq_2, belns_dir_path


class TestMapperManager(unittest.TestCase):
    def setUp(self):
        self.mm = MapperManager('sqlite:///')

    def test_disease_equivalence(self):
        """Tests that the disease label and ID map to the same equivalence class"""

        ns1 = 'file://' + os.path.join(belns_dir_path, 'disease-ontology.belns')
        self.mm.ensure_equivalences('file://' + test_eq_1, ns1)
        x = self.mm.get_equivalence_by_entry(ns1, "Alzheimer's disease")
        self.assertEqual('0b20937b-5eb4-4c04-8033-63b981decce7', x)

        ns2 = 'file://' + os.path.join(belns_dir_path, 'mesh-diseases.belns')
        self.mm.ensure_equivalences('file://' + test_eq_2, ns2)
        y = self.mm.get_equivalence_by_entry(ns2, "Alzheimer Disease")
        self.assertEqual('0b20937b-5eb4-4c04-8033-63b981decce7', y)

        d_expected = {
            ns1: "Alzheimer's disease",
            ns2: "Alzheimer Disease"
        }
        d = self.mm.get_equivalent_members(ns2, "Alzheimer Disease")

        self.assertEqual(d_expected, d)
