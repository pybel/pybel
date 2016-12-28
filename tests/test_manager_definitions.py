import os
import tempfile
import unittest
from datetime import datetime

from sqlalchemy import MetaData, Table

import tests.constants
from pybel.manager import defaults
from pybel.manager.cache import CacheManager
from pybel.manager.models import OWL_TABLE_NAME
from tests.constants import wine_iri

MGI_NAMESPACE = 'http://resource.belframework.org/belframework/20150611/namespace/mgi-mouse-genes.belns'
HGNC_NAMESPACE = 'http://resource.belframework.org/belframework/20150611/namespace/hgnc-human-genes.belns'

CELLSTRUCTURE_ANNOTATION = 'http://resource.belframework.org/belframework/20150611/annotation/cell-structure.belanno'
CELL_ANNOTATION = 'http://resource.belframework.org/belframework/20150611/annotation/cell.belanno'

defaults.default_namespaces = [
    MGI_NAMESPACE,
    HGNC_NAMESPACE
]

defaults.default_annotations = [
    CELLSTRUCTURE_ANNOTATION,
    CELL_ANNOTATION
]

dir_path = os.path.dirname(os.path.realpath(__file__))

test_ns1 = 'file:///' + tests.constants.test_ns_1
test_ns2 = 'file:///' + tests.constants.test_ns_2
test_an1 = 'file:///' + tests.constants.test_an_1


class TestCachePersistient(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.dir, 'test.db')
        self.connection = 'sqlite:///' + self.db_path

    def tearDown(self):
        os.remove(self.db_path)
        os.rmdir(self.dir)

    def test_insert_namespace(self):
        cm1 = CacheManager(connection=self.connection)

        cm1.ensure_namespace(MGI_NAMESPACE)
        self.assertIn(MGI_NAMESPACE, cm1.namespace_cache)
        self.assertIn('Oprk1', cm1.namespace_cache[MGI_NAMESPACE])
        self.assertEqual(set('GRP'), cm1.namespace_cache[MGI_NAMESPACE]['Oprk1'])
        self.assertIn('Gm16328', cm1.namespace_cache[MGI_NAMESPACE])
        self.assertEqual(set('GR'), cm1.namespace_cache[MGI_NAMESPACE]['Gm16328'])

        cm2 = CacheManager(connection=self.connection)

        cm2.ensure_namespace(MGI_NAMESPACE)
        self.assertIn(MGI_NAMESPACE, cm2.namespace_cache)
        self.assertIn('Oprk1', cm2.namespace_cache[MGI_NAMESPACE])
        self.assertEqual(set('GRP'), cm2.namespace_cache[MGI_NAMESPACE]['Oprk1'])
        self.assertIn('Gm16328', cm2.namespace_cache[MGI_NAMESPACE])
        self.assertEqual(set('GR'), cm2.namespace_cache[MGI_NAMESPACE]['Gm16328'])


class TestCache(unittest.TestCase):
    def setUp(self):
        self.connection = 'sqlite:///'
        self.cm = CacheManager(connection=self.connection, create_all=True)

    def test_existence(self):
        metadata = MetaData(self.cm.engine)
        table = Table(OWL_TABLE_NAME, metadata, autoload=True)
        self.assertIsNotNone(table)

    def test_insert_namespace(self):
        self.cm.ensure_namespace(MGI_NAMESPACE)
        self.assertIn(MGI_NAMESPACE, self.cm.namespace_cache)
        self.assertIn('Oprk1', self.cm.namespace_cache[MGI_NAMESPACE])
        self.assertEqual(set('GRP'), self.cm.namespace_cache[MGI_NAMESPACE]['Oprk1'])
        self.assertIn('Gm16328', self.cm.namespace_cache[MGI_NAMESPACE])
        self.assertEqual(set('GR'), self.cm.namespace_cache[MGI_NAMESPACE]['Gm16328'])

    def test_insert_annotation(self):
        self.cm.ensure_annotation(CELL_ANNOTATION)
        self.assertIn(CELL_ANNOTATION, self.cm.annotation_cache)
        self.assertIn('B cell', self.cm.annotation_cache[CELL_ANNOTATION])
        self.assertEqual('CL_0000236', self.cm.annotation_cache[CELL_ANNOTATION]['B cell'])

    def test_insert_owl(self):
        self.cm.ensure_owl(wine_iri)
        self.assertIn(wine_iri, self.cm.term_cache)
        self.assertIn('ChateauMorgon', self.cm.term_cache[wine_iri])
        self.assertIn('Winery', self.cm.term_cache[wine_iri])


class TestCacheKono(unittest.TestCase):
    def setUp(self):
        self.test_db = 'sqlite:///'

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

        test_db = CacheManager(self.test_db, setup_default_cache=True)
        for ns_key in defaults.default_namespaces:
            self.assertIn(ns_key, test_db.namespace_cache.keys())

        for an_key in defaults.default_annotations:
            self.assertIn(an_key, test_db.annotation_cache.keys())

        self.assertEqual(expected_check, test_db.check_definition('CHEBIID', definition_type='N'))

        self.assertIn('APP', test_db.namespace_cache[ns])

        self.assertIn('brain', test_db.annotation_cache[an])

        test_db.namespace_cache = {}
        test_db.annotation_cache = {}

        test_db.ensure_cache()

        for ns_key in defaults.default_namespaces:
            self.assertIn(ns_key, test_db.namespace_cache.keys())

        for an_key in defaults.default_annotations:
            self.assertIn(an_key, test_db.annotation_cache.keys())

        fake_ns_key = 'http://resource.belframework.org/belframework/20150611/namespace/chebi-ids.belns341'
        fake_an_key = 'http://resource.belframework.org/belframework/20150611/annotation/anatomyOGER.belanno'

        self.assertNotIn(fake_ns_key, test_db.namespace_cache.keys())
        self.assertNotIn(an, test_db.namespace_cache.keys())
        self.assertNotIn(fake_an_key, test_db.annotation_cache.keys())
        self.assertNotIn(ns, test_db.annotation_cache.keys())

    def test_setupWith_ensureCache(self):
        test_db = CacheManager(self.test_db)
        test_db.ensure_cache([test_ns1], [test_an1])

        self.assertIn(test_ns1, test_db.namespace_cache.keys())
        self.assertIn(test_an1, test_db.annotation_cache.keys())

        test_db2 = CacheManager(self.test_db)
        test_db2.setup_database(drop_existing=True)
        test_db2.ensure_cache([test_ns2], [test_an1])

        self.assertIn(test_ns2, test_db2.namespace_cache.keys())
        self.assertIn(test_an1, test_db2.annotation_cache.keys())

    def test_setupWith_updateCache(self):
        test_db = CacheManager(self.test_db)
        test_db.update_definition_cache([test_ns1], [test_an1])

        self.assertIn(test_ns1, test_db.namespace_cache.keys())
        self.assertIn(test_an1, test_db.annotation_cache.keys())

        test_db.namespace_cache = {}
        test_db.annotation_cache = {}
        test_db.ensure_cache()

        self.assertIn(test_ns1, test_db.namespace_cache.keys())
        self.assertIn(test_an1, test_db.annotation_cache.keys())

        test_db2 = CacheManager(self.test_db)
        test_db2.setup_database()
        test_db2.ensure_cache([test_ns1], [test_an1])

        self.assertIn(test_ns1, test_db2.namespace_cache.keys())
        self.assertIn(test_an1, test_db2.annotation_cache.keys())

    def test_allreadyIn(self):

        test_db = CacheManager(connection=self.test_db, setup_default_cache=False)
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

        test_db = CacheManager(self.test_db, setup_default_cache=False)
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

        test_db = CacheManager(self.test_db, setup_default_cache=False)
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

        test_db2 = CacheManager(self.test_db, setup_default_cache=False)
        test_db2.setup_database(drop_existing=True)
        test_db2.ensure_cache(self.test_namespace)

        check_result_before2 = test_db2.check_definition("TESTNS1", definition_type='N')
        self.assertIsNotNone(check_result_before2)

        test_db2.update_definition(test_ns2, overwrite_old_definition=True)
        self.assertNotEqual(self.expected_test_ns_cache, test_db2.namespace_cache)
        self.assertNotEqual(expected_cache_dict2, test_db2.namespace_cache)
        self.assertEqual(expected_cache_dict3, test_db2.namespace_cache)

        test_db2.namespace_cache = {}
        test_db2.ensure_cache([test_ns2])

        self.assertIn(test_ns2, test_db2.namespace_cache.keys())

    def test_update_namespaceCache(self):
        test_db = CacheManager(connection=self.test_db, setup_default_cache=False)
        test_db.update_definition_cache()
        test_db_keys = test_db.namespace_cache.keys()
        for db_key in defaults.default_namespaces:
            self.assertIn(db_key, test_db_keys)

        ns_removed = 'http://resource.belframework.org/belframework/20150611/namespace/hgnc-human-genes.belns'
        ns_to_add = 'http://resource.belframework.org/belframework/20131211/namespace/hgnc-human-genes.belns'

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
