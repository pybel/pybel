# -*- coding: utf-8 -*-

"""This module tests the to_json functions for all of the database models."""

import datetime
import json
import unittest

from pybel.constants import (
    CITATION_TYPE_PUBMED, IDENTIFIER,
    METADATA_AUTHORS, METADATA_CONTACT, METADATA_COPYRIGHT, METADATA_DESCRIPTION, METADATA_DISCLAIMER,
    METADATA_LICENSES, METADATA_NAME, METADATA_VERSION, NAME, NAMESPACE, NAMESPACE_DOMAIN_OTHER,
)
from pybel.language import citation_dict
from pybel.manager.models import Citation, Namespace, NamespaceEntry, Network
from pybel.testing.utils import n


class TestNetwork(unittest.TestCase):

    def setUp(self):
        self.name = n()
        self.version = n()
        self.created = datetime.datetime.utcnow()

        self.model = Network(
            name=self.name,
            version=self.version,
            created=self.created,
        )
        self.expected = {
            METADATA_NAME: self.name,
            METADATA_VERSION: self.version,
            'created': str(self.created),
        }

    def test_to_json(self):
        model_json = self.model.to_json()

        self.assertIn(METADATA_NAME, model_json)
        self.assertEqual(self.name, model_json[METADATA_NAME])
        self.assertIn(METADATA_VERSION, model_json)
        self.assertEqual(self.version, model_json[METADATA_VERSION])
        self.assertIn('created', model_json)
        self.assertEqual(str(self.created), model_json['created'])

        self.assertEqual(self.expected, model_json)

    def test_dump(self):
        json.dumps(self.model)

    def test_network(self):
        self.expected[METADATA_AUTHORS] = self.model.authors = n()
        self.assertEqual(self.expected, self.model.to_json())

        self.expected[METADATA_CONTACT] = self.model.contact = n()
        self.assertEqual(self.expected, self.model.to_json())

        self.expected[METADATA_DESCRIPTION] = self.model.description = n()
        self.assertEqual(self.expected, self.model.to_json())

        self.expected[METADATA_COPYRIGHT] = self.model.copyright = n()
        self.assertEqual(self.expected, self.model.to_json())

        self.expected[METADATA_DISCLAIMER] = self.model.disclaimer = n()
        self.assertEqual(self.expected, self.model.to_json())

        self.expected[METADATA_LICENSES] = self.model.licenses = n()
        self.assertEqual(self.expected, self.model.to_json())

        self.expected['id'] = None
        self.assertEqual(self.expected, self.model.to_json(include_id=True))


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
            contact='cthoyt@gmail.com',
            uploaded=uploaded,
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
            pattern=r'\w+',
            name='Test Namespace',
            domain=NAMESPACE_DOMAIN_OTHER,
            species='9606',
            version='1.0.0',
            author='Charles Tapley Hoyt',
            contact='cthoyt@gmail.com',
            uploaded=uploaded,
        )

        expected = dict(
            keyword='TEST',
            pattern=r'\w+',
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
            NAME: 'entry',
        }

        self.assertEqual(model.to_json(), expected)

        expected['id'] = model.id = 1

        self.assertEqual(model.to_json(include_id=True), expected)

        expected[IDENTIFIER] = model.identifier = 'test:00001'

        self.assertEqual(model.to_json(include_id=True), expected)

    def test_citation(self):
        db_id = n()
        model = Citation(
            db=CITATION_TYPE_PUBMED,
            db_id=db_id,
        )

        expected = citation_dict(namespace=CITATION_TYPE_PUBMED, identifier=db_id)
        self.assertEqual(expected, model.to_json())

        expected[NAME] = model.title = n()
        self.assertEqual(expected, model.to_json())
