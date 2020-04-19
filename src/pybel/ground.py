# -*- coding: utf-8 -*-

"""Grounding BEL JSON."""

import logging
from typing import List, Mapping, Optional, Tuple

import pyobo
from protmapper.uniprot_client import get_mnemonic
from pyobo.identifier_utils import normalize_prefix
from tqdm import tqdm

from .constants import (
    CONCEPT, FUSION, IDENTIFIER, MEMBERS, NAME, NAMESPACE, PARTNER_3P, PARTNER_5P, PRODUCTS,
    REACTANTS,
)
from .io import from_nodelink, to_nodelink
from .struct import BELGraph

__all__ = [
    'ground_nodelink',
    'ground_graph',
]

logger = logging.getLogger(__name__)
SKIP = {'ncbigene', 'pubchem.compound'}
NO_NAMES = {'fplx', 'eccode', 'dbsnp'}


def ground_graph(
    graph: BELGraph,
    prefixes: Optional[List[str]] = None,
    remapping: Optional[Mapping[Tuple[str, str], Tuple[str, str]]] = None,
) -> BELGraph:
    """Ground all entities in a BEL graph."""
    j = to_nodelink(graph)
    ground_nodelink(j, prefixes=prefixes, remapping=remapping)
    return from_nodelink(j)


def ground_nodelink(
    j,
    prefixes: Optional[List[str]] = None,
    remapping: Optional[Mapping[Tuple[str, str], Tuple[str, str]]] = None,
) -> None:
    """Ground entities in a nodelink data structure."""
    if prefixes is None:
        prefixes = (
            'hgnc', 'chebi', 'mgi', 'rgd', 'efo', 'ncbitaxon', 'conso',
            'go', 'mesh', 'hgnc.genefamily', 'hp', 'doid', 'interpro',
        )
    if remapping is None:
        remapping = {}

    name_to_ids = {
        prefix: pyobo.get_name_id_mapping(prefix)
        for prefix in prefixes
    }

    for node in tqdm(j['nodes'], desc='mapping nodes'):
        _process_concept(node, name_to_ids, remapping)
        _process_members(node, name_to_ids, remapping, MEMBERS)
        _process_members(node, name_to_ids, remapping, REACTANTS)
        _process_members(node, name_to_ids, remapping, PRODUCTS)
        _process_fusion(node, name_to_ids, remapping)


_UNHANDLED_NAMESPACES = set()


def _process_concept(node, name_to_ids, remapping):
    concept = node.get(CONCEPT)
    if concept is None:
        return

    name = concept[NAME]
    namespace = concept[NAMESPACE]

    if namespace.lower() in {'text', 'fixme'}:
        return

    if (namespace, name) in remapping:
        return remapping[namespace, name]

    norm_namespace = normalize_prefix(namespace)
    if norm_namespace is None:
        logger.warning('could not normalize namespace for %s ! %s', namespace, name)
        return
    elif norm_namespace in SKIP:
        return
    concept[NAMESPACE] = norm_namespace
    if norm_namespace in NO_NAMES:
        concept[IDENTIFIER] = name
    elif norm_namespace == 'uniprot':
        identifier = concept.get(IDENTIFIER)
        if identifier is not None:
            concept[NAME] = get_mnemonic(identifier, web_fallback=True)
        else:  # assume identifier given as name
            mnemomic = get_mnemonic(name, web_fallback=True)
            concept[IDENTIFIER] = name
            concept[NAME] = mnemomic
    elif norm_namespace in name_to_ids:
        identifier = name_to_ids[norm_namespace].get(name)
        if identifier is None:
            logger.warning('could not look up %s ! %s', norm_namespace, name)
            return
        concept[IDENTIFIER] = identifier
    elif norm_namespace not in _UNHANDLED_NAMESPACES:
        _UNHANDLED_NAMESPACES.add(norm_namespace)
        logger.warning('unhandled namespace: %s for %s', norm_namespace, node)


def _process_fusion(node, name_to_ids, remapping):
    fusion = node.get(FUSION)
    if not fusion:
        return
    _process_concept(fusion[PARTNER_3P], name_to_ids, remapping)
    _process_concept(fusion[PARTNER_5P], name_to_ids, remapping)


def _process_members(node, name_to_ids, remapping, key):
    members = node.get(key)
    if not members:
        return
    for member in members:
        _process_concept(member, name_to_ids, remapping)
