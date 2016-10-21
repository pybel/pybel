import os
import unittest
from datetime import datetime

from pybel.manager.defaults import default_namespaces as expected_keys
from pybel.manager.namespace_cache import NamespaceCache

dir_path = os.path.dirname(os.path.realpath(__file__))

test_ns1 = 'file:///' + os.path.join(dir_path, 'bel', 'test_ns_1.belns')
test_ns2 = 'file:///' + os.path.join(dir_path, 'bel', "test_ns_1_updated.belns")


class TestNsCache(unittest.TestCase):
    def setUp(self):
        self.test_db = 'sqlite://'
        self.data = os.path.join(dir_path, 'bel')

        self.test_namespace = [
            test_ns1
        ]

        self.expected_test_cache = {
            test_ns1: {
                'TestValue1': 'O',
                'TestValue2': 'O',
                'TestValue3': 'O',
                'TestValue4': 'O',
                'TestValue5': 'O'
            }
        }

    def test_setup(self):

        expected_check = {
            'keyword': 'CHEBIID',
            'version': '20150611',
            'url': 'http://resource.belframework.org/belframework/20150611/namespace/chebi-ids.belns',
            'createdDateTime': datetime(2015, 6, 11, 19, 51, 16),
            'pubDate': datetime(2015, 6, 1, 0, 0),
            'copyright': 'Copyright (c) 2015, OpenBEL Project. This work is licensed under a Creative Commons Attribution 3.0 Unported License.',
            'author': 'OpenBEL',
            'contact': 'info@openbel.org'
        }

        test_db = NamespaceCache(self.test_db, setup_default_cache=True)
        test_db_keys = test_db.cache.keys()
        for db_key in expected_keys:
            self.assertTrue(db_key in test_db_keys)

        app_in_hgnc = 'APP' in test_db.cache[
            'http://resource.belframework.org/belframework/20150611/namespace/hgnc-human-genes.belns']
        self.assertTrue(app_in_hgnc)

        test_db.ensure_cache()
        test_db_keys = test_db.cache.keys()
        for db_key in expected_keys:
            self.assertTrue(db_key in test_db_keys)

        fake_key = 'http://resource.belframework.org/belframework/20150611/namespace/chebi-ids.belns341'
        self.assertFalse(fake_key in test_db_keys)

    def test_allreadyIn(self):

        test_db = NamespaceCache(self.test_db, setup_default_cache=False)
        test_db.setup_database()

        for namespace in self.test_namespace:
            namespace_exists = test_db.check_namespace(namespace)
            self.assertIsNone(namespace_exists)

    def test_importing(self):

        expected_result = {
            'keyword': 'TESTNS1',
            'version': '1.0.0',
            'url': test_ns1,
            'createdDateTime': datetime(2016, 9, 17, 20, 50),
            'pubDate': None,
            'copyright': 'Copyright (c) Charles Tapley Hoyt. All Rights Reserved.',
            'author': 'Charles Tapley Hoyt',
            'contact': 'charles.hoyt@scai.fraunhofer.de'
        }

        test_db = NamespaceCache(self.test_db, setup_default_cache=False)
        test_db.setup_database(drop_existing=True)
        test_db.ensure_cache(self.test_namespace)
        print(test_db.cache)
        self.assertEqual(self.expected_test_cache, test_db.cache)

        self.assertEqual(expected_result, test_db.check_namespace('TESTNS1'))

        test_db.remove_namespace(test_ns1, '2016-09-17T20:50:00')

        self.assertIsNone(test_db.check_namespace("TESTNS1"))

    def test_update_namespace(self):

        expected_cache_dict2 = {
            test_ns1: {
                'TestValue1': 'O',
                'TestValue2': 'O',
                'TestValue3': 'O',
                'TestValue4': 'O',
                'TestValue5': 'O'
            },
            test_ns2: {
                'ImprovedTestValue1': 'O',
                'TestValue2': 'O',
                'TestValue3': 'O',
                'ImprovedTestValue4': 'O',
                'TestValue5': 'O',
                'AdditionalValue6': 'O'
            }
        }

        expected_cache_dict3 = {
            test_ns2: {
                'ImprovedTestValue1': 'O',
                'TestValue2': 'O',
                'TestValue3': 'O',
                'ImprovedTestValue4': 'O',
                'TestValue5': 'O',
                'AdditionalValue6': 'O'
            }
        }

        test_db = NamespaceCache(self.test_db, setup_default_cache=False)
        test_db.setup_database(drop_existing=True)
        test_db.ensure_cache(self.test_namespace)

        check_result_before = test_db.check_namespace("TESTNS1")
        self.assertIsNotNone(check_result_before)
        self.assertEqual(self.expected_test_cache, test_db.cache)
        self.assertNotEqual(expected_cache_dict2, test_db.cache)
        self.assertNotEqual(expected_cache_dict3, test_db.cache)

        test_db.update_namespace(test_ns2, remove_old_namespace=False)
        self.assertNotEqual(self.expected_test_cache, test_db.cache)
        self.assertEqual(expected_cache_dict2, test_db.cache)
        self.assertNotEqual(expected_cache_dict3, test_db.cache)

        test_db2 = NamespaceCache(self.test_db, setup_default_cache=False)
        test_db2.setup_database(drop_existing=True)
        test_db2.ensure_cache(self.test_namespace)

        check_result_before2 = test_db2.check_namespace("TESTNS1")
        self.assertIsNotNone(check_result_before2)

        test_db2.update_namespace(test_ns2, remove_old_namespace=True)
        self.assertNotEqual(self.expected_test_cache, test_db2.cache)
        self.assertNotEqual(expected_cache_dict2, test_db2.cache)
        self.assertEqual(expected_cache_dict3, test_db2.cache)

    def test_update_namespaceCache(self):
        test_db = NamespaceCache(self.test_db, setup_default_cache=False)
        test_db.update_namespace_cache()
        test_db_keys = test_db.cache.keys()
        for db_key in expected_keys:
            self.assertIn(db_key, test_db_keys)

        ns_removed = 'http://resource.belframework.org/belframework/20150611/namespace/hgnc-human-genes.belns'
        ns_to_add = 'http://resource.belframework.org/belframework/20131211/namespace/hgnc-human-genes.belns'

        test_db.remove_namespace(ns_removed, '2015-06-11T19:51:19')

        self.assertNotIn(ns_removed, test_db.cache.keys())

        test_db.update_namespace(ns_to_add)
        self.assertIn(ns_to_add, test_db.cache.keys())

        ns_to_update = 'http://resource.belframework.org/belframework/20150611/namespace/hgnc-human-genes.belns'
        test_db.update_namespace(ns_to_update)

        self.assertIn(ns_to_update, test_db.cache.keys())
        self.assertNotIn(ns_to_add, test_db.cache.keys())
