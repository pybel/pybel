# -*- coding: utf-8 -*-

import json
import logging
import os
import time

import pybel
from pybel.manager import Manager
from pybel.manager.citation_utils import enrich_pubmed_citations
from pybel.struct.mutation import strip_annotations

log = logging.getLogger('test')


def upload_cbn_dir(dir_path, manager):
    """Uploads CBN data to edge store

    :param str dir_path: Directory full of CBN JGIF files
    :param pybel.Manager manager:
    """
    t = time.time()

    for jfg_path in os.listdir(dir_path):
        if not jfg_path.endswith('.jgf'):
            continue

        path = os.path.join(dir_path, jfg_path)

        log.info('opening %s', path)

        with open(path) as f:
            cbn_jgif_dict = json.load(f)

        graph = pybel.from_cbn_jgif(cbn_jgif_dict)

        out_path = os.path.join(dir_path, jfg_path.replace('.jgf', '.bel'))
        with open(out_path, 'w') as o:
            pybel.to_bel_script(graph, o)

        strip_annotations(graph)
        enrich_pubmed_citations(manager=manager, graph=graph)
        pybel.to_database(graph, manager=manager)

        log.info('')

    log.info('done in %.2f', time.time() - t)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    log.setLevel(logging.INFO)
    logging.getLogger('pybel.parser.baseparser').setLevel(logging.WARNING)

    bms_base = os.environ['BMS_BASE']
    cbn_base = os.path.join(bms_base, 'cbn', 'Human-2.0')

    m = Manager()

    upload_cbn_dir(cbn_base, m)
