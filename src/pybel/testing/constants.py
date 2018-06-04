# -*- coding: utf-8 -*-

"""Testing resources for PyBEL."""

import os
from pathlib import Path

__all__ = [
    # BELNS
    'test_ns_1',
    'test_ns_2',
    'test_ns_nocache',
    'test_ns_nocache_path',
    'test_ns_empty',
    # BELANNO
    'test_an_1',
    # BEL
    'test_bel_simple',
    'test_bel_slushy',
    'test_bel_thorough',
    'test_bel_isolated',
    'test_bel_misordered',
    'test_bel_no_identifier_valiation',
    # JSON
    'test_jgif_path',

]

HERE = os.path.dirname(os.path.realpath(__file__))

resources_dir = os.path.join(HERE, 'resources')

# BELNS Files
belns_dir_path = os.path.join(resources_dir, 'belns')

test_ns_1 = os.path.join(belns_dir_path, 'test_ns_1.belns')
test_ns_2 = os.path.join(belns_dir_path, 'test_ns_1_updated.belns')
test_ns_nocache = os.path.join(belns_dir_path, 'test_nocache.belns')
test_ns_nocache_path = Path(test_ns_nocache).as_uri()
test_ns_empty = os.path.join(belns_dir_path, 'test_ns_empty.belns')

# BELANNO Files
belanno_dir_path = os.path.join(resources_dir, 'belanno')

test_an_1 = os.path.join(belanno_dir_path, 'test_an_1.belanno')

# BEL Files
bel_dir_path = os.path.join(resources_dir, 'bel')

test_bel_simple = os.path.join(bel_dir_path, 'test_bel.bel')
test_bel_slushy = os.path.join(bel_dir_path, 'slushy.bel')
test_bel_thorough = os.path.join(bel_dir_path, 'thorough.bel')
test_bel_isolated = os.path.join(bel_dir_path, 'isolated.bel')
test_bel_misordered = os.path.join(bel_dir_path, 'misordered.bel')
test_bel_no_identifier_valiation = os.path.join(bel_dir_path, 'no_identifier_validation_test.bel')

# JSON Files

test_jgif_path = os.path.join(bel_dir_path, 'Cytotoxic T-cell Signaling-2.0-Hs.json')
