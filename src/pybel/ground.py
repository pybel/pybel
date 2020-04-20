# -*- coding: utf-8 -*-

"""Grounding BEL JSON."""

import logging
import unittest
from typing import Tuple, Union

from protmapper.uniprot_client import get_mnemonic
from pyobo.extract import get_id_name_mapping, get_name_id_mapping
from pyobo.getters import NoOboFoundry
from pyobo.identifier_utils import normalize_prefix
from pyobo.xrefdb.sources.famplex import get_remapping
from tqdm import tqdm

from pybel.constants import (
    CONCEPT, FUSION, IDENTIFIER, MEMBERS, NAME, NAMESPACE, PARTNER_3P, PARTNER_5P, PRODUCTS,
    REACTANTS,
)
from pybel.io import from_nodelink, to_nodelink
from pybel.struct import BELGraph

__all__ = [
    'ground_nodelink',
    'ground_graph',
    'ground_node',
]

logger = logging.getLogger(__name__)
SKIP = {'ncbigene', 'pubchem.compound'}
NO_NAMES = {'fplx', 'eccode', 'dbsnp'}

# TODO will get updated
_REMAPPING = get_remapping()


def _get_remapping(prefix, name) -> Union[Tuple[str, str, str], Tuple[None, None, None]]:
    return _REMAPPING.get((prefix, name), (None, None, None))


def ground_graph(graph: BELGraph) -> BELGraph:
    """Ground all entities in a BEL graph."""
    j = to_nodelink(graph)
    ground_nodelink(j)
    return from_nodelink(j)


def ground_nodelink(j) -> None:
    """Ground entities in a nodelink data structure."""
    for node in tqdm(j['nodes'], desc='mapping nodes'):
        ground_node(node)


_UNHANDLED_NAMESPACES = set()


def ground_node(node) -> None:
    """Process a node JSON object, in place."""
    _process_concept(node)
    _process_members(node, MEMBERS)
    _process_members(node, REACTANTS)
    _process_members(node, PRODUCTS)
    _process_fusion(node)


def _process_concept(node) -> None:
    """Process a node JSON object."""
    concept = node.get(CONCEPT)
    if concept is None:
        return

    namespace = concept[NAMESPACE]
    if namespace.lower() in {'text', 'fixme'}:
        return

    prefix = normalize_prefix(namespace)
    if prefix is None:
        logger.warning('could not normalize namespace: %s', namespace)
        return

    concept[NAMESPACE] = prefix

    identifier = concept.get(IDENTIFIER)
    if identifier:  # don't trust whatever was put for the name, even if it's available
        _handle_identifier_not_name(concept=concept, prefix=prefix, identifier=identifier)
        return

    name = concept.get(NAME)
    _handle_name_and_not_identifier(concept=concept, prefix=prefix, name=name)


def _handle_identifier_not_name(*, concept, prefix, identifier) -> None:
    id_name_mapping = get_id_name_mapping(prefix)
    if id_name_mapping is None:
        logger.warning('could not get names for prefix %s', prefix)
        return
    name = id_name_mapping.get(identifier)
    if name is None:
        logger.warning('could not get name for %s:%s', prefix, identifier)
        return
    concept[NAME] = name
    return


def _handle_name_and_not_identifier(*, concept, prefix, name) -> None:
    remapped_prefix, remapped_identifier, remapped_name = _get_remapping(prefix, name)
    if remapped_prefix:
        concept[NAMESPACE] = remapped_prefix
        concept[IDENTIFIER] = remapped_identifier
        concept[NAME] = remapped_name
        return

    # Some namespaces are just too much of a problem at the moment to look up
    if prefix in SKIP:
        return

    concept[NAMESPACE] = prefix
    if prefix in NO_NAMES:
        concept[IDENTIFIER] = name
        return

    if prefix == 'uniprot':
        identifier = concept.get(IDENTIFIER)
        if identifier is not None:
            concept[NAME] = get_mnemonic(identifier, web_fallback=True)
            return

        # assume identifier given as name
        mnemomic = get_mnemonic(name, web_fallback=True)
        concept[IDENTIFIER] = name
        concept[NAME] = mnemomic
        return

    try:
        id_name_mapping = get_name_id_mapping(prefix)
    except NoOboFoundry:
        id_name_mapping = None

    if id_name_mapping is None:
        logger.warning('unhandled namespace in %s ! %s', prefix, name)
        return

    identifier = id_name_mapping.get(name)
    if identifier is None:
        logger.warning('could not find name %s in namespace %s', name, prefix)
        return

    concept[IDENTIFIER] = identifier


def _process_fusion(node) -> None:
    fusion = node.get(FUSION)
    if not fusion:
        return
    _process_concept(fusion[PARTNER_3P])
    _process_concept(fusion[PARTNER_5P])


def _process_members(node, key) -> None:
    members = node.get(key)
    if not members:
        return
    for member in members:
        _process_concept(member)


class TestGround(unittest.TestCase):
    """Test grounding."""

    def _test_ground(self, expected, result):
        ground_node(result)
        self.assertEqual(expected, result)

    def test_normalize_prefix_case(self):
        """Test that the prefix is normalized to the correct case."""
        self._test_ground(
            {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'},
            {NAMESPACE: 'MESH', NAME: 'Neurons', IDENTIFIER: 'D009474'}
        )

    def test_normalize_prefix_synonym(self):
        """Test that the prefix is normalized by a synonym."""
        self._test_ground(
            {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'},
            {NAMESPACE: 'MESHA', NAME: 'Neurons', IDENTIFIER: 'D009474'}
        )

    def test_add_identifier(self):
        """Test that the identifier can get looked up."""
        self._test_ground(
            {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'},
            {NAMESPACE: 'MESH', NAME: 'Neurons'}
        )

    def test_add_identifier_fix_wrong_name(self):
        """Test that the name is replaced if the identifier is already available.."""
        self._test_ground(
            {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'},
            {NAMESPACE: 'MESH', NAME: 'Nonsense name!', IDENTIFIER: 'D009474'}
        )

    def test_remap(self):
        """Test remapping using FamPlex."""
        self._test_ground(
            {NAMESPACE: 'fplx', NAME: 'TAP', IDENTIFIER: 'TAP'},
            {NAMESPACE: 'SFAM', NAME: 'TAP Family'},
        )
        self._test_ground(
            {NAMESPACE: 'fplx', NAME: 'Gamma_secretase', IDENTIFIER: 'Gamma_secretase'},
            {NAMESPACE: 'SCOMP', NAME: 'gamma Secretase Complex'},
        )
