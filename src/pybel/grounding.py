# -*- coding: utf-8 -*-

"""Grounding for PyBEL.

Why does this module exist, even though BEL relies on definitions of external vocabularies?

BEL namespaces only have names, and there's no standard for mapping back to identifiers.
PyBEL has a internal rule that for any given namespace, it will try and look up another
"identifier" space in the same directory. However, this is an implementation detail and does

This module uses PyOBO to look the identifiers for nodes in a BEL graph when possible
or replace the label given with BEP-0008 (OBO-style) syntax. It also normalizes namespace
names to their standards, as defined by Identifiers.org/OBOFoundry/PyOBO internal standard.

Finally, it has a tool that allows for the definition of remapping of namespace/name pairs.
Right now, it's only set up to use the FamPlex mappings, but it will be made more extensible
to help support the clean-up of curation efforts that created their own low-quality terminologies
(publicly accessible examples include the Selventa Large Corpus, Selventa Small Corpus, HemeKG,
covid19kg, and the Causal Biological Networks database).

After installation with ``pip install git+https://github.com/hemekg/hemekg.git``, it can be run with:

.. code-block:: python

    import hemekg
    heme_graph = hemekg.get_graph()

    import pybel.grounding
    pybel.grounding.ground(heme_graph)

After installation with ``pip install git+https://github.com/covid19kg/covid19kg.git``, it can be run with:

.. code-block:: python

    import covid19kg
    covid19_graph = covid19kg.get_graph()

    import pybel.grounding
    pybel.grounding.ground(covid19_graph)

After installation with ``pip install git+https://github.com/cthoyt/selventa-knowledge.git``, it can be run with:

.. code-block:: python

    import selventa_knowledge
    selventa_graph = selventa_knowledge.get_graph()

    import pybel.grounding
    pybel.grounding.ground(selventa_graph)
"""

import logging
import unittest
from typing import Tuple, Union

from protmapper.uniprot_client import get_id_from_mnemonic, get_mnemonic
from pyobo.extract import get_id_name_mapping, get_name_id_mapping
from pyobo.getters import NoOboFoundry
from pyobo.identifier_utils import normalize_prefix
from pyobo.xrefdb.sources.famplex import get_remapping
from tqdm import tqdm

from pybel.constants import (
    CONCEPT, FUSION, GMOD, IDENTIFIER, KIND, MEMBERS, NAME, NAMESPACE, PARTNER_3P, PARTNER_5P, PMOD, PRODUCTS,
    REACTANTS, VARIANTS,
)
from pybel.io import from_nodelink, to_nodelink
from pybel.language import gmod_mappings, pmod_mappings
from pybel.struct import BELGraph

__all__ = [
    'ground',
    'ground_nodelink',
]

logger = logging.getLogger(__name__)
SKIP = {'ncbigene', 'pubchem.compound'}
NO_NAMES = {'fplx', 'eccode', 'dbsnp'}

# TODO will get updated
_REMAPPING = get_remapping()


def _get_remapping(prefix: str, name: str) -> Union[Tuple[str, str, str], Tuple[None, None, None]]:
    return _REMAPPING.get((prefix, name), (None, None, None))


def ground(graph: BELGraph) -> BELGraph:
    """Ground all entities in a BEL graph."""
    j = to_nodelink(graph)
    ground_nodelink(j)
    return from_nodelink(j)


def ground_nodelink(graph_nodelink_dict) -> None:
    """Ground entities in a nodelink data structure."""
    for node in tqdm(graph_nodelink_dict['nodes'], desc='mapping nodes'):
        _process_node(node)

    # TODO ground entities in edges! what about all those fabulous activities?


_UNHANDLED_NAMESPACES = set()


def _process_node(node) -> None:
    """Process a node JSON object, in place."""
    if CONCEPT in node:
        _process_concept(node[CONCEPT])
    if VARIANTS in node:
        _process_list(node[VARIANTS])
    if MEMBERS in node:
        _process_list(node[MEMBERS])
    if REACTANTS in node:
        _process_list(node[REACTANTS])
    if PRODUCTS in node:
        _process_list(node[PRODUCTS])
    if FUSION in node:
        _process_fusion(node[FUSION])


def _process_concept(concept) -> None:
    """Process a node JSON object."""
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
    if prefix == 'uniprot':
        concept[NAME] = get_mnemonic(identifier)
        return

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

    if prefix == 'bel' and KIND in concept:
        kind = concept[KIND]
        if kind == PMOD and name in pmod_mappings:
            # the 0th position xref is the preferred one (usually GO)
            _mapped = pmod_mappings[name]['xrefs'][0]
        elif kind == GMOD and name in gmod_mappings:
            _mapped = gmod_mappings[name]['xrefs'][0]
        else:
            raise ValueError(f'invalid kind: {kind}')
        concept[NAMESPACE] = _mapped[NAMESPACE]
        concept[IDENTIFIER] = _mapped[IDENTIFIER]
        concept[NAME] = _mapped[NAME]
        return

    if prefix == 'uniprot':
        # assume identifier given as name
        identifier = get_id_from_mnemonic(name)
        if identifier is not None:
            concept[IDENTIFIER] = identifier
            return

        mnemomic = get_mnemonic(name, web_fallback=True)
        if mnemomic is not None:
            concept[IDENTIFIER] = name
            concept[NAME] = mnemomic
            return

        logger.warning('could not interpret uniprot name: %s', name)
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


def _process_fusion(fusion) -> None:
    _process_concept(fusion[PARTNER_3P])
    _process_concept(fusion[PARTNER_5P])


def _process_list(members) -> None:
    for member in members:
        _process_concept(member)


class TestGround(unittest.TestCase):
    """Test grounding."""

    def test_process_concept(self):
        """Test several cases in processing concepts."""
        r = [
            (
                'Normalize prefix to correct case',
                {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'},
                {NAMESPACE: 'MESH', NAME: 'Neurons', IDENTIFIER: 'D009474'},
            ),
            (
                'Normalize prefix by synonym',
                {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'},
                {NAMESPACE: 'MESHA', NAME: 'Neurons', IDENTIFIER: 'D009474'},
            ),
            (
                'Look up identifier by name',
                {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'},
                {NAMESPACE: 'MESH', NAME: 'Neurons'},
            ),
            (
                'Lookup by UniProt identifier as name',
                {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
                {NAMESPACE: 'UniProt', NAME: 'O60921'},
            ),
            (
                'Lookup by UniProt mnemonic as name',
                {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
                {NAMESPACE: 'UniProt', NAME: 'HUS1_HUMAN'},
            ),
            (
                'Rewrite wrong UniProt name',
                {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
                {NAMESPACE: 'UniProt', NAME: 'WRONG!!!!', IDENTIFIER: 'O60921'},
            ),
            (
                'Overwrite name by identifier',
                {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'},
                {NAMESPACE: 'MESH', NAME: 'Nonsense name!', IDENTIFIER: 'D009474'},
            ),
            (
                'Remap example 1',
                {NAMESPACE: 'fplx', NAME: 'TAP', IDENTIFIER: 'TAP'},
                {NAMESPACE: 'SFAM', NAME: 'TAP Family'},
            ),
            (
                'Remap example 2',
                {NAMESPACE: 'fplx', NAME: 'Gamma_secretase', IDENTIFIER: 'Gamma_secretase'},
                {NAMESPACE: 'SCOMP', NAME: 'gamma Secretase Complex'},
            ),
        ]
        for name, expected, result in r:
            with self.subTest(name=name):
                _process_concept(result)
                self.assertEqual(expected, result)

    def test_process_nodes(self):
        """Test several cases dealing with full nodes."""
        r = [
            (
                'Look up identifier of member by name',
                {MEMBERS: [{NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'}]},
                {MEMBERS: [{NAMESPACE: 'MESH', NAME: 'Neurons'}]},
            ),
            (
                'Look up identifier of member by name AND name of complex',
                {
                    CONCEPT: {NAMESPACE: 'complexportal', NAME: 'Checkpoint clamp complex', IDENTIFIER: 'CPX-1829'},
                    MEMBERS: [
                        {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
                        {NAMESPACE: 'uniprot', NAME: 'RAD9A_HUMAN', IDENTIFIER: 'Q99638'},
                        {NAMESPACE: 'uniprot', NAME: 'RAD1_HUMAN', IDENTIFIER: 'O60671'},
                    ]
                },
                {
                    CONCEPT: {NAMESPACE: 'complexportal', NAME: 'Checkpoint clamp complex'},
                    MEMBERS: [
                        {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN'},
                        {NAMESPACE: 'uniprot', NAME: 'RAD9A_HUMAN'},
                        {NAMESPACE: 'uniprot', NAME: 'RAD1_HUMAN'},
                    ]
                },
            ),
            (
                'Normalize pmod by name',
                {
                    CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
                    VARIANTS: [{NAMESPACE: 'go', IDENTIFIER: '0006468', NAME: 'protein phosphorylation'}]
                },
                {
                    CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN'},
                    VARIANTS: [{NAMESPACE: 'GO', NAME: 'protein phosphorylation'}]
                },
            ),
            (
                'Fix name in pmod by identifier lookup',
                {
                    CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
                    VARIANTS: [{NAMESPACE: 'go', IDENTIFIER: '0006468', NAME: 'protein phosphorylation'}]
                },
                {
                    CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN'},
                    VARIANTS: [{NAMESPACE: 'GO', IDENTIFIER: '0006468', NAME: 'WRONG!'}]
                },
            ),
            (
                'Normalize pmod using default BEL namespace',
                {
                    CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
                    VARIANTS: [{NAMESPACE: 'go', IDENTIFIER: '0006468', NAME: 'protein phosphorylation', KIND: PMOD}]
                },
                {
                    CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN'},
                    VARIANTS: [{NAMESPACE: 'bel', NAME: 'Ph', KIND: PMOD}]
                },
            ),
            (
                'Normalize pmod using default BEL namespace - Me (to investigate conflict with gmod)',
                {
                    CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
                    VARIANTS: [{NAMESPACE: 'go', IDENTIFIER: '0006479', NAME: 'protein methylation', KIND: PMOD}]
                },
                {
                    CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN'},
                    VARIANTS: [{NAMESPACE: 'bel', NAME: 'Me', KIND: PMOD}]
                },
            ),
            (
                'Normalize gmod using default BEL namespace - Me (to investigate conflict with pmod)',
                {
                    CONCEPT: {NAMESPACE: 'hgnc', NAME: 'MAPT', IDENTIFIER: '6893'},
                    VARIANTS: [{NAMESPACE: 'go', IDENTIFIER: '0006306', NAME: 'DNA methylation', KIND: GMOD}]
                },
                {
                    CONCEPT: {NAMESPACE: 'HGNC', NAME: 'MAPT'},
                    VARIANTS: [{NAMESPACE: 'bel', NAME: 'Me', KIND: GMOD}]
                },
            ),
        ]
        for name, expected, result in r:
            with self.subTest(name=name):
                _process_node(result)
                self.assertEqual(expected, result)

# TODO look up members when checking a named complex, protein family, or pathway
