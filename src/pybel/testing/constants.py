# -*- coding: utf-8 -*-

import logging
import os
import tempfile
import unittest
from json import dumps
from pathlib import Path
from requests.compat import urlparse

from pybel import BELGraph
from pybel.constants import *
from pybel.dsl import *
from pybel.manager import Manager
from pybel.parser.exc import *
from pybel.parser.parse_bel import BelParser
from pybel.utils import subdict_matches

log = logging.getLogger(__name__)

dir_path = os.path.dirname(os.path.realpath(__file__))
resources_dir_path = os.path.join(dir_path, 'resources')
bel_dir_path = os.path.join(resources_dir_path, 'bel')
belns_dir_path = os.path.join(resources_dir_path, 'belns')
belanno_dir_path = os.path.join(resources_dir_path, 'belanno')

test_bel_simple = os.path.join(bel_dir_path, 'test_bel.bel')
test_bel_slushy = os.path.join(bel_dir_path, 'slushy.bel')
test_bel_thorough = os.path.join(bel_dir_path, 'thorough.bel')
test_bel_isolated = os.path.join(bel_dir_path, 'isolated.bel')
test_bel_misordered = os.path.join(bel_dir_path, 'misordered.bel')
test_bel_no_identifier_valiation = os.path.join(bel_dir_path, 'no_identifier_validation_test.bel')

test_an_1 = os.path.join(belanno_dir_path, 'test_an_1.belanno')

test_ns_1 = os.path.join(belns_dir_path, 'test_ns_1.belns')
test_ns_2 = os.path.join(belns_dir_path, 'test_ns_1_updated.belns')
test_ns_nocache = os.path.join(belns_dir_path, 'test_nocache.belns')
test_ns_empty = os.path.join(belns_dir_path, 'test_ns_empty.belns')

test_ns_nocache_path = Path(test_ns_nocache).as_uri()


test_connection = os.environ.get('PYBEL_TEST_CONNECTION')
