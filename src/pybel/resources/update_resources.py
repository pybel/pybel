# -*- coding: utf-8 -*-

"""URLs for default BEL resources.

This script is susceptible to rate limits from the GitHub API, so don't run it over and over!
"""

import logging
import os

from bel_resources.github import get_famplex_url, get_github_url

HERE = os.path.abspath(os.path.dirname(__file__))

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('pybel').setLevel(logging.DEBUG)


def _get_conso_url(name):
    return get_github_url(
        owner='pharmacome',
        repo='conso',
        path='external/{}.belns'.format(name),
    )


variables = dict(
    CHEBI_URL='chebi-names',
    EC_URL='ec-code',
    FB_URL='fb-names',
    GO_URL='go-names',
    HGNC_URL='hgnc-names',
    MESH_URL='mesh-names',
    MGI_URL='mgi-names',
    NCBIGENE_URL='ncbigene-names',
    RGD_URL='rgd-names',
)


def main():
    """Update the resources links file."""
    with open(os.path.join(HERE, 'resources.py'), 'w') as file:
        print('# -*- coding: utf-8 -*-\n', file=file)
        print('"""Resources for PyBEL."""\n', file=file)
        for k, v in sorted(variables.items()):
            print("{} = '{}'".format(k, _get_conso_url(v)), file=file)
        print("\nFPLX_URL = '{}'".format(get_famplex_url()), file=file)


if __name__ == '__main__':
    main()
