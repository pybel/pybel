# -*- coding: utf-8 -*-

"""Test cases for PyBEL testing."""

import logging
import os
import tempfile
import unittest

from ..manager import Manager

__all__ = [
    'TEST_CONNECTION',
    'TemporaryCacheMixin',
    'TemporaryCacheClsMixin',
    'FleetingTemporaryCacheMixin',
]

log = logging.getLogger(__name__)

TEST_CONNECTION = os.environ.get('PYBEL_TEST_CONNECTION')


class TemporaryCacheMixin(unittest.TestCase):
    """A test case that has a connection and a manager that is created for each test function."""

    def setUp(self):
        """Set up the test function with a connection and manager."""
        if TEST_CONNECTION:
            self.connection = TEST_CONNECTION
        else:
            self.fd, self.path = tempfile.mkstemp()
            self.connection = 'sqlite:///' + self.path
            log.info('Test generated connection string %s', self.connection)

        self.manager = Manager(connection=self.connection)
        self.manager.create_all()

    def tearDown(self):
        """Tear down the test functing by closing the session and removing the database."""
        self.manager.session.close()

        if not TEST_CONNECTION:
            os.close(self.fd)
            os.remove(self.path)
        else:
            self.manager.drop_all()


class TemporaryCacheClsMixin(unittest.TestCase):
    """A test case that has a connection and a manager that is created for each test class."""

    fd, path, manager = None, None, None

    @classmethod
    def setUpClass(cls):
        """Set up the test class with a connection and manager."""
        if TEST_CONNECTION:
            cls.connection = TEST_CONNECTION
        else:
            cls.fd, cls.path = tempfile.mkstemp()
            cls.connection = 'sqlite:///' + cls.path
            log.info('Test generated connection string %s', cls.connection)

        cls.manager = Manager(connection=cls.connection)
        cls.manager.create_all()

    @classmethod
    def tearDownClass(cls):
        """Tear down the test class by closing the session and removing the database."""
        cls.manager.session.close()

        if not TEST_CONNECTION:
            os.close(cls.fd)
            os.remove(cls.path)
        else:
            cls.manager.drop_all()


class FleetingTemporaryCacheMixin(TemporaryCacheClsMixin):
    """A test case that clears the database before each function."""

    def setUp(self):
        """Set up the function by clearing the database."""
        super(FleetingTemporaryCacheMixin, self).setUp()

        self.manager.drop_networks()
        self.manager.drop_edges()
        self.manager.drop_nodes()
        self.manager.drop_namespaces()
