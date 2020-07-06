# -*- coding: utf-8 -*-

"""Utilities for SBGN-ML conversion."""

import logging
from typing import Iterable, Optional, Tuple
from urllib.parse import unquote_plus

from pyobo.identifier_utils import normalize_prefix

from .constants import RDF, hgnc_name_to_id

logger = logging.getLogger(__name__)


def _get_label(glyph, sbgn_prefix) -> Optional[str]:
    _labels = list({
        label.get('text')
        for label in glyph.findall(f'{sbgn_prefix}label')
    })
    return _labels[0] if _labels else None


def _iter_references(glyph, sbgn_prefix) -> Iterable[Tuple[str, str]]:
    _xpath = f"{sbgn_prefix}extension/annotation/{RDF}RDF/{RDF}Description/"
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
                elif r.startswith('https://identifiers.org/'):
                    prefix, identifier = r[len('https://identifiers.org/'):].split(':')
                    norm_prefix = normalize_prefix(prefix)
                    if norm_prefix is None:
                        logger.warning('unhandled prefix: %s', prefix)
                        continue
                    yield norm_prefix, identifier
                elif r.startswith('http://identifiers.org/'):  # TODO i don't like that this logic is redundant
                    prefix, identifier = r[len('http://identifiers.org/'):].split(':')
                    norm_prefix = normalize_prefix(prefix)
                    if norm_prefix is None:
                        logger.warning('unhandled prefix: %s', prefix)
                        continue
                    yield norm_prefix, identifier
                elif r.startswith('urn:miriam:'):
                    r = r[len('urn:miriam:'):]
                    for sf in [
                        'kegg.pathway',
                        'kegg.reaction',
                        'ncbigene',
                        'uniprot',
                        'pubmed',
                        'hgnc',
                        'ncbiprotein',
                        'drugbank',
                        'taxonomy',
                        'interpro',
                        'pubchem.compound',
                        'refseq',
                    ]:
                        if r.startswith(sf):
                            yield sf, r[len(sf) + 1:]  # +1 is because of the colon ":"
                            break
                    else:
                        logger.warning(f'unhandled urn:miriam resource: %s', r)

                else:
                    logger.warning(f'unhandled resource: %s', r)
                    continue
