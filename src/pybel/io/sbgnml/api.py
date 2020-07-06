# -*- coding: utf-8 -*-

"""Convert parsed SBGN-ML to BEL."""

from typing import Optional, TextIO, Union

from networkx.utils import open_file

from pybel.io.sbgnml import convert_sbgn, parse_sbgn, parse_sbgn_url
from pybel.struct.graph import BELGraph

__all__ = [
    'from_sbgn_url',
    'from_sbgn_file',
]


@open_file(0, mode='r')
def from_sbgn_file(path: Union[str, TextIO], version: Optional[str] = None) -> BELGraph:
    """Convert a SBGN-ML file."""
    return convert_sbgn(parse_sbgn(path, version=version))


def from_sbgn_url(url: str, version: Optional[str] = None) -> BELGraph:
    """Convert a SBGN-ML file by URL."""
    return convert_sbgn(parse_sbgn_url(url, version=version))


if __name__ == '__main__':
    _url = 'https://git-r3lab.uni.lu/covid/models/-/raw/master/Curation/IL6-AMP/IL6-AMP.AF.sbgn'
    x = from_sbgn_url(_url)
    print(x)
