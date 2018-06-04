# -*- coding: utf-8 -*-

"""Mocks for PyBEL testing."""

import os

from .constants import bel_dir_path, belanno_dir_path, belns_dir_path
from .utils import get_uri_name
from ..constants import GOCC_LATEST

try:
    from unittest import mock
except ImportError:
    import mock

__all__ = [
    'MockResponse',
    'MockSession',
    'mock_bel_resources',
]


class MockResponse:
    """See http://stackoverflow.com/questions/15753390/python-mock-requests-and-the-response"""

    def __init__(self, mock_url):
        if mock_url == GOCC_LATEST:
            self.path = os.path.join(belns_dir_path, 'go-cellular-component.belns')
        elif mock_url.endswith('hgnc-human-genes-20170725.belns'):
            self.path = os.path.join(belns_dir_path, 'hgnc-human-genes.belns')
        elif mock_url.endswith('chebi-20170725.belns'):
            self.path = os.path.join(belns_dir_path, 'chebi.belns')
        elif mock_url.endswith('go-biological-process-20170725.belns'):
            self.path = os.path.join(belns_dir_path, 'go-biological-process.belns')
        elif mock_url.endswith('species-taxonomy-id-20170511.belanno'):
            self.path = os.path.join(belanno_dir_path, 'species-taxonomy-id.belanno')
        elif mock_url.endswith('confidence-1.0.0.belanno'):
            self.path = os.path.join(belanno_dir_path, 'confidence-1.0.0.belanno')
        elif mock_url.endswith('.belns'):
            self.path = os.path.join(belns_dir_path, get_uri_name(mock_url))
        elif mock_url.endswith('.belanno'):
            self.path = os.path.join(belanno_dir_path, get_uri_name(mock_url))
        elif mock_url.endswith('.bel'):
            self.path = os.path.join(bel_dir_path, get_uri_name(mock_url))
        else:
            raise ValueError('Invalid extension')

        if not os.path.exists(self.path):
            raise ValueError("file doesn't exist: {}".format(self.path))

    def iter_lines(self):
        with open(self.path, 'rb') as file:
            lines = list(file)

        for line in lines:
            yield line

    def raise_for_status(self):
        pass


class MockSession:
    """Patches the session object so requests can be redirected through the filesystem without rewriting BEL files"""

    def __init__(self):
        pass

    def mount(self, prefix, adapter):
        pass

    @staticmethod
    def get(url):
        return MockResponse(url)

    def close(self):
        pass


mock_bel_resources = mock.patch('pybel.resources.utils.requests.Session', side_effect=MockSession)
