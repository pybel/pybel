# -*- coding: utf-8 -*-

"""Utilities for SBGN-ML conversion."""

import logging
from typing import Iterable, Optional, Tuple
from urllib.parse import unquote_plus

from pybel.io.sbgnml.constants import RDF, SBGN, hgnc_name_to_id

logger = logging.getLogger(__name__)


def _get_label(glyph) -> Optional[str]:
    _labels = list({
        label.get('text')
        for label in glyph.findall(f'{SBGN}label')
    })
    return _labels[0] if _labels else None


def _iter_references(glyph) -> Iterable[Tuple[str, str]]:
    _xpath = f"{SBGN}extension/annotation/{RDF}RDF/{RDF}Description/"
    for d in glyph.findall(_xpath):
        for bag in d:
            for y in bag:
                r = y.attrib[f'{RDF}resource']
                if r.startswith('urn:miriam:hgnc.symbol:'):
                    r = r[len('urn:miriam:hgnc.symbol:'):]
                    hgnc_id = hgnc_name_to_id.get(r)
                    if hgnc_id is None:
                        logger.warning(f'could not find HGNC symbol: %s', r)
                        continue
                    yield 'hgnc', hgnc_id
                elif r.startswith('urn:miriam:obo.chebi:CHEBI%3A'):
                    yield 'chebi', r[len('urn:miriam:obo.chebi:CHEBI%3A:'):]
                elif r.startswith('urn:miriam:hgnc:HGNC%3A'):
                    yield 'hgnc', r[len('urn:miriam:hgnc:HGNC%3A'):]
                elif r.startswith('urn:miriam:doi:'):
                    yield 'doi', unquote_plus(r[len('urn:miriam:doi:'):])
                elif r.startswith('urn:miriam:'):
                    r = r[len('urn:miriam:'):]
                    for sf in [
                        'kegg.pathway',
                        'ncbigene',
                        'uniprot',
                        'pubmed',
                        'hgnc',
                        'ncbiprotein',
                        'drugbank',
                    ]:
                        if r.startswith(sf):
                            yield sf, r[len(sf) + 1:]
                            break
                    else:
                        logger.warning(f'unhandled urn:miriam resource: %s', r)

                else:
                    logger.warning(f'unhandled resource: %s', r)
                    continue
