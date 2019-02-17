# -*- coding: utf-8 -*-

"""Mocks for PyBEL testing."""

import itertools as itt
import os
from unittest import mock

from .constants import bel_dir_path, belanno_dir_path, belns_dir_path
from .utils import get_uri_name

__all__ = [
    'MockResponse',
    'MockSession',
    'mock_bel_resources',
]

_responses = [
    ('go.belns', os.path.join(belns_dir_path, 'go.belns')),
    ('hgnc-human-genes-20170725.belns', os.path.join(belns_dir_path, 'hgnc-human-genes.belns')),
    ('chebi-20170725.belns', os.path.join(belns_dir_path, 'chebi.belns')),
    ('species-taxonomy-id-20170511.belanno', os.path.join(belanno_dir_path, 'species-taxonomy-id.belanno')),
    ('confidence-1.0.0.belanno', os.path.join(belanno_dir_path, 'confidence-1.0.0.belanno')),
]


class MockResponse:
    """See http://stackoverflow.com/questions/15753390/python-mock-requests-and-the-response."""

    def __init__(self, url_to_mock: str):
        """Build a mock for the requests Response object."""
        _r = [
            ('.belns', os.path.join(belns_dir_path, get_uri_name(url_to_mock))),
            ('.belanno', os.path.join(belanno_dir_path, get_uri_name(url_to_mock))),
            ('.bel', os.path.join(bel_dir_path, get_uri_name(url_to_mock))),
        ]

        self.path = None
        for suffix, path in itt.chain(_responses, _r):
            if url_to_mock.endswith(suffix):
                self.path = path
                break

        if self.path is None:
            raise ValueError('missing file')

        if not os.path.exists(self.path):
            raise ValueError("file doesn't exist: {}".format(self.path))

    def iter_lines(self):
        """Iterate the lines of the mock file."""
        with open(self.path, 'rb') as file:
            yield from file

    def raise_for_status(self):
        """Mock raising an error, by not doing anything at all."""


class MockSession:
    """Patches the session object so requests can be redirected through the filesystem without rewriting BEL files."""

    def mount(self, prefix, adapter):
        """Mock mounting an adapter by not doing anything."""

    @staticmethod
    def get(url: str):
        """Mock getting a URL by returning a mock response."""
        return MockResponse(url)

    def close(self):
        """Mock closing a connection by not doing anything."""


mock_bel_resources = mock.patch('bel_resources.utils.requests.Session', side_effect=MockSession)
