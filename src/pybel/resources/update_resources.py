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


keyword_to_suffix = dict(
    chebi='chebi-names',
    ec='ec-code',
    fb='fb-names',
    go='go-names',
    hgnc='hgnc-names',
    mesh='mesh-names',
    mgi='mgi-names',
    ncbigene='ncbigene-names',
    rgd='rgd-names',
)


def main():
    """Update the resources links file."""
    keyword_to_url = {
        keyword: _get_conso_url(suffix)
        for keyword, suffix in keyword_to_suffix.items()
    }

    with open(os.path.join(HERE, 'resources.py'), 'w') as file:
        print('# -*- coding: utf-8 -*-\n', file=file)
        print('"""Resources for PyBEL."""\n', file=file)
        for keyword, url in sorted(keyword_to_url.items()):
            print("{}_URL = '{}'".format(keyword.upper(), url), file=file)

        print("\nFPLX_URL = '{}'".format(get_famplex_url()), file=file)

        print('\n#: Default URL lookup for some keywords', file=file)
        print('keyword_to_url = dict(', file=file)
        for k in sorted(keyword_to_suffix):
            print('    {}={}_URL,'.format(k, k.upper()), file=file)
        print('    fplx=FPLX_URL,', file=file)
        print(')', file=file)


if __name__ == '__main__':
    main()
