import os
import tempfile
import unittest

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
        self.cm = CacheManager(connection=self.connection)

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
