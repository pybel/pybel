import os
import unittest
from datetime import datetime

from pybel.manager.defaults import default_annotations as expected_an_keys
from pybel.manager.defaults import default_namespaces as expected_ns_keys
from pybel.manager.namespace_cache import DefinitionCacheManager

dir_path = os.path.dirname(os.path.realpath(__file__))

test_ns1 = 'file:///' + os.path.join(dir_path, 'bel', 'test_ns_1.belns')
test_ns2 = 'file:///' + os.path.join(dir_path, 'bel', "test_ns_1_updated.belns")
test_an1 = 'file:///' + os.path.join(dir_path, 'bel', "test_an_1.belanno")


class TestNsCache(unittest.TestCase):
    def setUp(self):
        self.test_db = 'sqlite://'
        self.data = os.path.join(dir_path, 'bel')

        self.test_namespace = [
            test_ns1
        ]

        self.test_annotation = [
            test_an1
        ]

        self.expected_test_ns_cache = {
            test_ns1: {
                'TestValue1': 'O',
                'TestValue2': 'O',
                'TestValue3': 'O',
                'TestValue4': 'O',
                'TestValue5': 'O'
            }
        }

        self._expected_test_an_cache = {
            test_an1: {
                'TestAnnot1': 'O',
                'TestAnnot2': 'O',
                'TestAnnot3': 'O',
                'TestAnnot4': 'O',
                'TestAnnot5': 'O'
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

        ns = 'http://resource.belframework.org/belframework/20150611/namespace/hgnc-human-genes.belns'
        an = 'http://resource.belframework.org/belframework/20150611/annotation/anatomy.belanno'

        test_db = DefinitionCacheManager(self.test_db, setup_default_cache=True)
        for ns_key in expected_ns_keys:
            self.assertIn(ns_key, test_db.namespace_cache.keys())

        for an_key in expected_an_keys:
            self.assertIn(an_key, test_db.annotation_cache.keys())

        self.assertEqual(expected_check, test_db.check_definition('CHEBIID', definition_type='N'))

        app_in_hgnc = 'APP' in test_db.namespace_cache[ns]
        self.assertTrue(app_in_hgnc)

        brain_in_anatomy = 'brain' in test_db.annotation_cache[an]
        self.assertTrue(brain_in_anatomy)

        test_db.namespace_cache = {}
        test_db.annotation_cache = {}

        test_db.ensure_cache()

        for ns_key in expected_ns_keys:
            self.assertIn(ns_key, test_db.namespace_cache.keys())

        for an_key in expected_an_keys:
            self.assertIn(an_key, test_db.annotation_cache.keys())

        fake_ns_key = 'http://resource.belframework.org/belframework/20150611/namespace/chebi-ids.belns341'
        fake_an_key = 'http://resource.belframework.org/belframework/20150611/annotation/anatomyOGER.belanno'

        self.assertNotIn(fake_ns_key, test_db.namespace_cache.keys())
        self.assertNotIn(an, test_db.namespace_cache.keys())
        self.assertNotIn(fake_an_key, test_db.annotation_cache.keys())
        self.assertNotIn(ns, test_db.annotation_cache.keys())


    def test_setupWith_ensureCache(self):
        # 153 - 155
        test_db = DefinitionCacheManager(self.test_db)
        test_db.ensure_cache([test_ns1], [test_an1])

        self.assertIn(test_ns1, test_db.namespace_cache.keys())
        self.assertIn(test_an1, test_db.annotation_cache.keys())

        # 141 - 153
        test_db2 = DefinitionCacheManager(self.test_db)
        test_db2.setup_database(drop_existing=True)
        test_db2.ensure_cache([test_ns2], [test_an1])

        self.assertIn(test_ns2, test_db2.namespace_cache.keys())
        self.assertIn(test_an1, test_db2.annotation_cache.keys())

    def test_setupWith_updateCache(self):
        # 172 - 173
        test_db = DefinitionCacheManager(self.test_db)
        test_db.update_definition_cache([test_ns1], [test_an1])

        self.assertIn(test_ns1, test_db.namespace_cache.keys())
        self.assertIn(test_an1, test_db.annotation_cache.keys())

        # 141 - 153
        test_db.namespace_cache = {}
        test_db.annotation_cache = {}
        test_db.ensure_cache()

        self.assertIn(test_ns1, test_db.namespace_cache.keys())
        self.assertIn(test_an1, test_db.annotation_cache.keys())

        # 167 - 172
        test_db2 = DefinitionCacheManager(self.test_db)
        test_db2.setup_database()
        test_db2.ensure_cache([test_ns1], [test_an1])

        self.assertIn(test_ns1, test_db2.namespace_cache.keys())
        self.assertIn(test_an1, test_db2.annotation_cache.keys())

    def test_allreadyIn(self):

        test_db = DefinitionCacheManager(self.test_db, setup_default_cache=False)
        test_db.setup_database()

        for namespace in self.test_namespace:
            namespace_exists = test_db.check_definition(namespace, definition_type='N')
            self.assertIsNone(namespace_exists)

        for annotation in self.test_annotation:
            annotation_exists = test_db.check_definition(annotation, definition_type='A')
            self.assertIsNone(annotation_exists)

    def test_importing(self):

        expected_ns_result = {
            'keyword': 'TESTNS1',
            'version': '1.0.0',
            'url': test_ns1,
            'createdDateTime': datetime(2016, 9, 17, 20, 50),
            'pubDate': None,
            'copyright': 'Copyright (c) Charles Tapley Hoyt. All Rights Reserved.',
            'author': 'Charles Tapley Hoyt',
            'contact': 'charles.hoyt@scai.fraunhofer.de'
        }

        expected_an_result = {
            'keyword': 'TESTAN1',
            'version': '1.0.0',
            'url': test_an1,
            'createdDateTime': datetime(2016, 9, 17, 20, 50),
            'pubDate': None,
            'copyright': 'Copyright (c) Charles Tapley Hoyt. All Rights Reserved.',
            'author': 'Charles Tapley Hoyt',
            'contact': 'charles.hoyt@scai.fraunhofer.de'
        }

        test_db = DefinitionCacheManager(self.test_db, setup_default_cache=False)
        test_db.setup_database(drop_existing=True)
        test_db.ensure_cache(self.test_namespace, self.test_annotation)

        self.assertEqual(self.expected_test_ns_cache, test_db.namespace_cache)
        self.assertEqual(self._expected_test_an_cache, test_db.annotation_cache)

        self.assertEqual(expected_ns_result, test_db.check_definition('TESTNS1', definition_type='N'))
        self.assertEqual(expected_an_result, test_db.check_definition('TESTAN1', definition_type='A'))

        test_db.remove_definition(test_ns1, '2016-09-17T20:50:00')

        self.assertIsNone(test_db.check_definition("TESTNS1", definition_type='N'))

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

        test_db = DefinitionCacheManager(self.test_db, setup_default_cache=False)
        test_db.setup_database(drop_existing=True)
        test_db.ensure_cache(self.test_namespace)

        check_result_before = test_db.check_definition("TESTNS1", definition_type='N')
        self.assertIsNotNone(check_result_before)
        self.assertEqual(self.expected_test_ns_cache, test_db.namespace_cache)
        self.assertNotEqual(expected_cache_dict2, test_db.namespace_cache)
        self.assertNotEqual(expected_cache_dict3, test_db.namespace_cache)

        test_db.update_definition(test_ns2, overwrite_old_definition=False)
        self.assertNotEqual(self.expected_test_ns_cache, test_db.namespace_cache)
        self.assertEqual(expected_cache_dict2, test_db.namespace_cache)
        self.assertNotEqual(expected_cache_dict3, test_db.namespace_cache)

        test_db2 = DefinitionCacheManager(self.test_db, setup_default_cache=False)
        test_db2.setup_database(drop_existing=True)
        test_db2.ensure_cache(self.test_namespace)

        check_result_before2 = test_db2.check_definition("TESTNS1", definition_type='N')
        self.assertIsNotNone(check_result_before2)

        test_db2.update_definition(test_ns2, overwrite_old_definition=True)
        self.assertNotEqual(self.expected_test_ns_cache, test_db2.namespace_cache)
        self.assertNotEqual(expected_cache_dict2, test_db2.namespace_cache)
        self.assertEqual(expected_cache_dict3, test_db2.namespace_cache)

        # 187 - 189
        test_db2.namespace_cache = {}
        test_db2.ensure_cache([test_ns2])

        self.assertIn(test_ns2, test_db2.namespace_cache.keys())

    def test_update_namespaceCache(self):
        test_db = DefinitionCacheManager(self.test_db, setup_default_cache=False)
        test_db.update_definition_cache()
        test_db_keys = test_db.namespace_cache.keys()
        for db_key in expected_ns_keys:
            self.assertIn(db_key, test_db_keys)

        ns_removed = 'http://resource.belframework.org/belframework/20150611/namespace/hgnc-human-genes.belns'
        ns_to_add = 'http://resource.belframework.org/belframework/20131211/namespace/hgnc-human-genes.belns'

        # 245 - exit
        test_db.remove_definition(ns_removed, '2015-06-11T19:51:19')
        self.assertNotIn(ns_removed, test_db.namespace_cache.keys())

        test_db.update_definition(ns_to_add)
        self.assertIn(ns_to_add, test_db.namespace_cache.keys())

        ns_to_update = 'http://resource.belframework.org/belframework/20150611/namespace/hgnc-human-genes.belns'
        test_db.update_definition(ns_to_update, overwrite_old_definition=True)

        self.assertIn(ns_to_update, test_db.namespace_cache.keys())
        self.assertNotIn(ns_to_add, test_db.namespace_cache.keys())

        outdated_namespace = 'http://resource.belframework.org/belframework/1.0/namespace/entrez-gene-ids-hmr.belns'
        test_db.update_definition(outdated_namespace, overwrite_old_definition=False)
        self.assertIn(outdated_namespace, test_db.namespace_cache.keys())

        test_db.update_definition_cache([test_ns1, test_ns2])

        self.assertNotIn(test_ns1, test_db.namespace_cache.keys())
        self.assertIn(test_ns2, test_db.namespace_cache.keys())
