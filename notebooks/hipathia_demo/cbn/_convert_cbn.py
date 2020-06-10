# -*- coding: utf-8 -*-

"""Convert the `CausalBionet (CBN) <http://causalbionet.com>`_ for Hipathia."""

import json
import os
import zipfile
from urllib.request import urlretrieve

import click
from pyobo.cli_utils import verbose_option
from tqdm import tqdm

import pybel
import pybel.grounding

HERE = os.path.dirname(__file__)
OUTPUT = os.path.join(HERE, 'output')
SOURCE = os.path.join(HERE, 'source')
os.makedirs(OUTPUT, exist_ok=True)

# Get and unzip this in this directory
URL = 'http://causalbionet.com/Content/jgf_bulk_files/Human-2.0.zip'
PATH = os.path.join(HERE, 'Human-2.0.zip')


@click.command()
@verbose_option
def main():
    """Convert all CBN graphs to Hipathia."""
    if not os.path.exists(PATH):
        urlretrieve(URL, PATH)

    if not os.path.exists(SOURCE):
        with zipfile.ZipFile(PATH) as file:
            file.extractall(SOURCE)

    for filename in tqdm(os.listdir(SOURCE)):
        path = os.path.join(SOURCE, filename)
        with open(path) as f:
            cbn_jgif_dict = json.load(f)

        graph = pybel.from_cbn_jgif(cbn_jgif_dict)
        graph = pybel.grounding.ground(graph)
        pybel.to_hipathia(graph, OUTPUT)


if __name__ == '__main__':
    main()
