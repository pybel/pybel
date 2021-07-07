# -*- coding: utf-8 -*-

"""Ecosystem of Machine-maintained Models with Automated Analysis (EMMAA).

`EMMAA <https://emmaa.indra.bio/>`_ is a project built on top of INDRA by
the Sorger Lab at Harvard Medical School. It automatically builds knowledge
graphs around pathways/indications periodically (almost daily) using the
INDRA Database, which in turn is updated periodically (almost daily)
with the most recent literature from MEDLINE, PubMed Central, several
major publishers, and other bespoke text corpora such as CORD-19.
"""

import json
import logging
from typing import Iterable, Optional
from xml.etree import ElementTree  # noqa:S405

import click
import requests
from more_click import verbose_option

from .indra import from_indra_statements
from ..struct import BELGraph

__all__ = [
    'from_emmaa',
]

logger = logging.getLogger(__name__)


def from_emmaa(
    model: str, *,
    date: Optional[str] = None,
    extension: Optional[str] = None,
    suppress_warnings: bool = False,
) -> BELGraph:
    """Get an EMMAA model as a BEL graph.

    Get the most recent COVID-19 model from EMMAA with the following:

    .. code-block:: python

        import pybel

        covid19_emmaa_graph = pybel.from_emmaa('covid19', extension='jsonl')
        covid19_emmaa_graph.summarize()

    PyBEL does its best to look up the most recent model, but if that doesn't work,
    you can specify it explicitly with the ``date`` keyword argument in the form
    of ``%Y-%m-%d-%H-%M-%S`` like in the following:

    .. code-block:: python

        import pybel

        covid19_emmaa_graph = pybel.from_emmaa('covid19', '2020-04-23-17-44-57', extension='jsonl')
        covid19_emmaa_graph.summarize()
    """
    statements = get_statements_from_emmaa(
        model=model, date=date, extension=extension, suppress_warnings=suppress_warnings,
    )
    return from_indra_statements(statements, name=model, version=date)


def get_statements_from_emmaa(
    model: str, *,
    date: Optional[str] = None,
    extension: Optional[str] = None,
    suppress_warnings: bool = False,
):
    """Get INDRA statements from EMMAA.

    :rtype: List[indra.statements.Statement]
    """
    from indra.statements import stmts_from_json

    if suppress_warnings:
        logging.getLogger('indra.assemblers.pybel.assembler').setLevel(logging.ERROR)
        logging.getLogger('indra.sources.bel.processor').setLevel(logging.ERROR)
    if extension is None:
        extension = 'json'

    if date is None:
        url = f'https://emmaa.s3.amazonaws.com/assembled/{model}/latest_statements_{model}.{extension}'
    else:
        url = f'https://emmaa.s3.amazonaws.com/assembled/{model}/statements_{date}.{extension}'

    res = requests.get(url)

    if extension == 'jsonl':
        res_json = [
            json.loads(line)
            for line in res.text.splitlines()
        ]
        return stmts_from_json(res_json)
    elif extension == 'json':
        res_json = res.json()
        return stmts_from_json(res_json)
    elif extension == 'gz':
        raise NotImplementedError
    else:
        raise ValueError(f'unhandled extension: {extension}')


def _get_latest_date(model: str) -> str:
    res = requests.get('https://emmaa.s3.amazonaws.com/')
    tree = ElementTree.fromstring(res.text)  # noqa:S314
    return max(_iter_dates(tree, model))


def _iter_dates(tree: ElementTree, model: str) -> Iterable[str]:
    aws = '{http://s3.amazonaws.com/doc/2006-03-01/}'
    for x in tree.findall(f'{aws}Contents/{aws}Key'):
        prefix = f'assembled/{model}/statements_'
        if x.text.startswith(prefix):
            yield x.text


@click.command()
@verbose_option
@click.option('--extension', default='jsonl')
def main(extension: str):
    """Run the EMMAA converter."""
    from_emmaa('covid19', extension=extension).summarize()


if __name__ == '__main__':
    main()
