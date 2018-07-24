# -*- coding: utf-8 -*-

"""UnitTest cases for PyBEL testing."""

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
    def setUp(self):
        if TEST_CONNECTION:
            self.connection = TEST_CONNECTION
        else:
            self.fd, self.path = tempfile.mkstemp()
            self.connection = 'sqlite:///' + self.path
            log.info('Test generated connection string %s', self.connection)

        self.manager = Manager(connection=self.connection)
        self.manager.create_all()

    def tearDown(self):
        self.manager.session.close()

        if not TEST_CONNECTION:
            os.close(self.fd)
            os.remove(self.path)
        else:
            self.manager.drop_all()


class TemporaryCacheClsMixin(unittest.TestCase):
    """Facilitates generating a database in a temporary file on a class-by-class basis"""

    fd, path, manager = None, None, None

    @classmethod
    def setUpClass(cls):
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
        cls.manager.session.close()

        if not TEST_CONNECTION:
            os.close(cls.fd)
            os.remove(cls.path)
        else:
            cls.manager.drop_all()


class FleetingTemporaryCacheMixin(TemporaryCacheClsMixin):
    """This class makes a manager available for the entire existence of the class but deletes everything that gets
    stuck in it after each test"""

    def setUp(self):
        super(FleetingTemporaryCacheMixin, self).setUp()

        self.manager.drop_networks()
        self.manager.drop_edges()
        self.manager.drop_nodes()
        self.manager.drop_namespaces()
        self.manager.drop_annotations()
