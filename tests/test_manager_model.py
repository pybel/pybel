# -*- coding: utf-8 -*-

"""This module tests the to_json functions for all of the database models"""

import datetime
import unittest

from pybel.constants import *
from pybel.manager.models import *
from tests.utils import n


class TestModels(unittest.TestCase):
    def test_namespace_url(self):
        uploaded = datetime.datetime.now()

        model = Namespace(
            keyword='TEST',
            url='http://test.com',
            name='Test Namespace',
            domain=NAMESPACE_DOMAIN_OTHER,
            species='9606',
            version='1.0.0',
            author='Charles Tapley Hoyt',
            contact='charles.hoyt@scai.fraunhofer.de',
            uploaded=uploaded
        )

        expected = dict(
            keyword='TEST',
            url='http://test.com',
            name='Test Namespace',
            version='1.0.0',
        )

        self.assertEqual(model.to_json(), expected)

        expected['id'] = model.id = 1

        self.assertEqual(model.to_json(include_id=True), expected)

    def test_namespace_pattern(self):
        uploaded = datetime.datetime.now()

        model = Namespace(
            keyword='TEST',
            pattern='\w+',
            name='Test Namespace',
            domain=NAMESPACE_DOMAIN_OTHER,
            species='9606',
            version='1.0.0',
            author='Charles Tapley Hoyt',
            contact='charles.hoyt@scai.fraunhofer.de',
            uploaded=uploaded
        )

        expected = dict(
            keyword='TEST',
            pattern='\w+',
            name='Test Namespace',
            version='1.0.0',
        )

        self.assertEqual(model.to_json(), expected)

    def test_namespace_entry(self):
        model = NamespaceEntry(
            name='entry',
            namespace=Namespace(keyword='test')
        )

        expected = {
            NAMESPACE: 'test',
            NAME: 'entry'
        }

        self.assertEqual(model.to_json(), expected)

        expected['id'] = model.id = 1

        self.assertEqual(model.to_json(include_id=True), expected)

        expected[IDENTIFIER] = model.identifier = 'test:00001'

        self.assertEqual(model.to_json(include_id=True), expected)

    def test_annotation(self):
        uploaded = datetime.datetime.now()
        model = Annotation(
            uploaded=uploaded,
            keyword='TEST',
            url='http://test.com',
            name='Test Namespace',
            version='1.0.0',
            author='Charles Tapley Hoyt',
            contact='charles.hoyt@scai.fraunhofer.de',
        )

        expected = dict(
            keyword='TEST',
            url='http://test.com',
            name='Test Namespace',
            version='1.0.0',
        )

        self.assertEqual(model.to_json(), expected)

        expected['id'] = model.id

        self.assertEqual(model.to_json(include_id=True), expected)

    def test_annotation_entry(self):
        model = AnnotationEntry(
            name='entry',
            annotation=Annotation(
                keyword='test'
            )

        )

        expected = dict(
            annotation_keyword='test',
            annotation='entry'
        )

        self.assertEqual(model.to_json(), expected)

        expected['id'] = model.id = 1

        self.assertEqual(model.to_json(include_id=True), expected)

    def test_network(self):
        name = n()
        version = n()
        model = Network(
            name=name,
            version=version
        )
        expected = {
            METADATA_NAME: name,
            METADATA_VERSION: version,
            'created': None,
        }

        self.assertEqual(expected, model.to_json())

        expected[METADATA_AUTHORS] = model.authors = n()
        self.assertEqual(expected, model.to_json())

        expected[METADATA_CONTACT] = model.contact = n()
        self.assertEqual(expected, model.to_json())

        expected[METADATA_DESCRIPTION] = model.description = n()
        self.assertEqual(expected, model.to_json())

        expected[METADATA_COPYRIGHT] = model.copyright = n()
        self.assertEqual(expected, model.to_json())

        expected[METADATA_DISCLAIMER] = model.disclaimer = n()
        self.assertEqual(expected, model.to_json())

        expected[METADATA_LICENSES] = model.licenses = n()
        self.assertEqual(expected, model.to_json())

        expected['id'] = None
        self.assertEqual(expected, model.to_json(include_id=True))

    def test_citation(self):
        ref = n()
        model = Citation(
            type=CITATION_TYPE_PUBMED,
            reference=ref
        )
        expected = {
            CITATION_TYPE: CITATION_TYPE_PUBMED,
            CITATION_REFERENCE: ref
        }

        self.assertEqual(expected, model.to_json())

        expected[CITATION_TITLE] = model.title = n()
