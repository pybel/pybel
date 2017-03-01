import json
import logging
import os
import unittest

from pybel import from_path
from pybel.cx import to_cx_json
from tests.constants import test_bel_thorough

log = logging.getLogger(__name__)

output = os.path.expanduser('~/Desktop/results.txt')


@unittest.skipUnless('PYBEL2CX' in os.environ, 'Not in development environment for pybel and cx conversion')
class TestCx(unittest.TestCase):
    def test_cx_export(self):
        graph = from_path(test_bel_thorough, allow_nested=True)

        log.info('Graph size: %d', graph.number_of_nodes())

        cx = to_cx_json(graph)

        log.info('CX Size: %s', len(cx))

        with open(output, 'w') as f:
            json.dump(cx, f, indent=2)
