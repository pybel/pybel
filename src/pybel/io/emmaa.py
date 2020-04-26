# -*- coding: utf-8 -*-

"""Ecosystem of Machine-maintained Models with Automated Analysis (EMMAA)."""

from typing import Iterable, Optional
from xml.etree import ElementTree  # noqa:S405

import requests

from .indra import from_indra_statements_json
from ..struct import BELGraph

__all__ = [
    'from_emmaa',
]

URL_FORMAT = 'https://emmaa.s3.amazonaws.com/assembled/{}/statements_{}.json'
LISTING = 'https://emmaa.s3.amazonaws.com/'
NS = '{http://s3.amazonaws.com/doc/2006-03-01/}'


def from_emmaa(model: str, *, date: Optional[str] = None) -> BELGraph:
    """Get an EMMAA model as a BEL graph.

    Get the most recent COVID-19 model from EMMAA with the following:

    .. code-block:: python

        import pybel

        covid19_emmaa_graph = pybel.from_emmaa('covid19')
        covid19_emmaa_graph.summarize()

    PyBEL does its best to look up the most recent model, but if that doesn't work,
    you can specify it explicitly with the ``date`` keyword argument in the form
    of ``%Y-%m-%d %H:%M:%S`` like in the following:

    .. code-block:: python

        import pybel

        covid19_emmaa_graph = pybel.from_emmaa('covid19', '2020-04-23-17-44-57')
        covid19_emmaa_graph.summarize()
    """
    if date is None:
        date = _get_latest_date(model)

    url = URL_FORMAT.format(model, date)
    res = requests.get(url)
    res_json = res.json()
    graph = from_indra_statements_json(res_json)
    graph.name = model
    graph.version = date
    return graph


def _get_latest_date(model: str) -> str:
    res = requests.get(LISTING)
    tree = ElementTree.fromstring(res.content.decode('utf-8'))  # noqa:S314
    return max(_iter_dates(tree, model))


def _iter_dates(tree, model: str) -> Iterable[str]:
    for x in tree.findall('{aws}Contents/{aws}Key'.format(aws=NS)):
        prefix = 'assembled/{}/statements_'.format(model)
        if x.text.startswith(prefix):
            yield x.text[len(prefix):-len('.json')]
