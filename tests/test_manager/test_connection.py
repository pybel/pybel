# -*- coding: utf-8 -*-

"""Tests for instantiating the manager"""

import os
import tempfile
import unittest

from pybel import Manager
from pybel.manager.base_manager import build_engine_session

try:
    from unittest import mock
except ImportError:
    import mock


class TestInstantiation(unittest.TestCase):
    """Allows for testing with a consistent connection without changing the configuration."""

    def setUp(self):
        """Add two class-level variables: ``mock_global_connection`` and ``mock_module_connection`` that can be
        used as context managers to mock the bio2bel connection getter functions."""

        self.fd, self.path = tempfile.mkstemp()
        self.connection = 'sqlite:///' + self.path

        def mock_connection():
            """Get the connection enclosed by this class.

            :rtype: str
            """
            return self.connection

        self.mock_connection = mock.patch('pybel.manager.cache_manager.get_cache_connection', mock_connection)

    def tearDown(self):
        os.close(self.fd)
        os.remove(self.path)

    def test_fail_connection_none(self):
        """Test that a None causes a huge error."""
        with self.assertRaises(ValueError):
            build_engine_session(None)

    def test_instantiate_init(self):
        """Test what happens when no connection is specified for the normal constructor."""
        with self.mock_connection:
            manager = Manager()
            self.assertEqual(self.connection, str(manager.engine.url))

    def test_instantiate_manager_positional(self):
        manager = Manager(self.connection)
        self.assertEqual(self.connection, str(manager.engine.url))

    def test_instantiate_manager_positional_with_keyword(self):
        manager = Manager(self.connection, echo=True)
        self.assertEqual(self.connection, str(manager.engine.url))

    def test_instantiate_manager_fail_positional(self):
        with self.assertRaises(ValueError):
            Manager(self.connection, True)

    def test_instantiate_manager_keyword(self):
        manager = Manager(connection=self.connection)
        self.assertEqual(self.connection, str(manager.engine.url))

    def test_instantiate_manager_connection_fail_too_many_keyword(self):
        with self.assertRaises(ValueError):
            Manager(connection=self.connection, engine='something', session='something')

    def test_instantiate_manager_engine_fail_too_many_keywords(self):
        with self.assertRaises(ValueError):
            Manager(engine='something', session='something', echo=True)

    def test_instantiate_manager_engine_missing(self):
        with self.assertRaises(ValueError):
            Manager(engine=None, session='fake-session')

    def test_instantiate_manager_session_missing(self):
        with self.assertRaises(ValueError):
            Manager(engine='fake-engine', session=None)
