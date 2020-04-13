# -*- coding: utf-8 -*-

"""Convert the `CausalBionet (CBN) <http://causalbionet.com>`_ for Hipathia."""

import json
import os

from tqdm import tqdm

import pybel
import pybel.ground

# Get and unzip this in this directory
URL = 'http://causalbionet.com/Content/jgf_bulk_files/Human-2.0.zip'

HERE = os.path.dirname(__file__)
JGIF_DIR = os.path.join(os.path.expanduser('~'), 'Downloads', 'Human-2.0')


def main():
    """Convert all CBN graphs to Hipathia."""
    for filename in tqdm(os.listdir(JGIF_DIR)):
        path = os.path.join(JGIF_DIR, filename)
        with open(path) as f:
            cbn_jgif_dict = json.load(f)

        graph = pybel.from_cbn_jgif(cbn_jgif_dict)
        graph = pybel.ground.ground_graph(graph)
        pybel.to_hipathia(graph, HERE)


if __name__ == '__main__':
    main()
