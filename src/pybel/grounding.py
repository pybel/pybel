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
from pyobo.identifier_utils import SYNONYM_TO_KEY, normalize_prefix
from pyobo.xrefdb.sources.famplex import get_remapping
from tqdm import tqdm

from pybel.constants import (
    CONCEPT, FUSION, GMOD, IDENTIFIER, KIND, MEMBERS, NAME, NAMESPACE, PARTNER_3P, PARTNER_5P, PMOD, PRODUCTS,
    REACTANTS, VARIANTS,
)
from pybel.io import from_nodelink, to_nodelink
from pybel.language import gmod_mappings, pmod_mappings
from pybel.struct import BELGraph, get_namespaces, get_ungrounded_nodes

__all__ = [
    'ground',
    'ground_nodelink',
]

logger = logging.getLogger(__name__)
SKIP = {'ncbigene', 'pubchem.compound'}
NO_NAMES = {'fplx', 'eccode', 'dbsnp'}

# TODO will get updated
_NAME_REMAPPING = get_remapping()
_ID_REMAPPING = {}


def _get_name_remapping(prefix: str, name: str) -> Union[Tuple[str, str, str], Tuple[None, None, None]]:
    return _NAME_REMAPPING.get((prefix, name), (None, None, None))


def _get_id_remapping(prefix: str, identifier: str) -> Union[Tuple[str, str, str], Tuple[None, None, None]]:
    return _ID_REMAPPING.get((prefix, identifier), (None, None, None))


def ground(graph: BELGraph, remove_ungrounded: bool = True) -> BELGraph:
    """Ground all entities in a BEL graph."""
    j = to_nodelink(graph)
    ground_nodelink(j)
    graph = from_nodelink(j)

    if remove_ungrounded:
        ungrounded_nodes = get_ungrounded_nodes(graph)
        graph.remove_nodes_from(ungrounded_nodes)
        graph.namespace_url.clear()
        graph.namespace_pattern.update({
            namespace: '.*'
            for namespace in get_namespaces(graph)
        })

    return graph


def ground_nodelink(graph_nodelink_dict) -> None:
    """Ground entities in a nodelink data structure."""
    name = graph_nodelink_dict.get('graph', {}).get('name', 'graph')
    node_it = tqdm(graph_nodelink_dict['nodes'], desc='grounding nodes in {}'.format(name))
    for node in node_it:
        _process_node(node)

    # TODO ground entities in edges! what about all those fabulous activities?


_UNHANDLED_NAMESPACES = set()


def _process_node(node) -> bool:
    """Process a node JSON object, in place.

    :return: If all parts of the node were successfully grounded
    """
    success = True
    if CONCEPT in node:
        success = success and _process_concept(node=node)
    if VARIANTS in node:
        success = success and _process_list(node[VARIANTS])
    if MEMBERS in node:
        success = success and _process_list(node[MEMBERS])
    if REACTANTS in node:
        success = success and _process_list(node[REACTANTS])
    if PRODUCTS in node:
        success = success and _process_list(node[PRODUCTS])
    if FUSION in node:
        success = success and _process_fusion(node[FUSION])
    return success


def _process_concept(*, node) -> bool:
    """Process a node JSON object."""
    concept = node[CONCEPT]
    namespace = concept[NAMESPACE]
    if namespace.lower() in {'text', 'fixme'}:
        return False

    prefix = normalize_prefix(namespace)
    if prefix is None:
        logger.warning('could not normalize namespace: %s', namespace)
        return False

    concept[NAMESPACE] = prefix

    identifier = concept.get(IDENTIFIER)
    name = concept.get(NAME)
    if identifier:  # don't trust whatever was put for the name, even if it's available
        map_success = _handle_identifier_not_name(concept=concept, prefix=prefix, identifier=identifier)
    else:
        map_success = _handle_name_and_not_identifier(node=node, concept=concept, prefix=prefix, name=name)

    if not map_success:
        return False

    _remap_by_identifier(concept)
    return True


def _remap_by_identifier(concept) -> bool:
    identifier = concept.get(IDENTIFIER)
    if identifier is None:
        return False
    namespace = concept[NAMESPACE]
    logger.debug('attempting to remap %s:%s', namespace, identifier)
    remapped_prefix, remapped_identifier, remapped_name = _get_id_remapping(namespace, identifier)
    logger.debug('remapping result %s:%s ! %s', remapped_prefix, remapped_identifier, remapped_name)
    if remapped_prefix:
        concept[NAMESPACE] = remapped_prefix
        concept[IDENTIFIER] = remapped_identifier
        concept[NAME] = remapped_name
        return True
    return False


def _handle_identifier_not_name(*, concept, prefix, identifier) -> bool:
    if prefix == 'uniprot':
        concept[NAME] = get_mnemonic(identifier)
        return True

    id_name_mapping = get_id_name_mapping(prefix)
    if id_name_mapping is None:
        logger.warning('could not get names for prefix %s', prefix)
        return False
    name = id_name_mapping.get(identifier)
    if name is None:
        logger.warning('could not get name for %s:%s', prefix, identifier)
        return False
    concept[NAME] = name

    return True


def _handle_name_and_not_identifier(*, node, concept, prefix, name) -> bool:
    remapped_prefix, remapped_identifier, remapped_name = _get_name_remapping(prefix, name)
    if remapped_prefix:
        concept[NAMESPACE] = remapped_prefix
        concept[IDENTIFIER] = remapped_identifier
        concept[NAME] = remapped_name
        return True

    # Some namespaces are just too much of a problem at the moment to look up
    if prefix in SKIP:
        return False

    concept[NAMESPACE] = prefix
    if prefix in NO_NAMES:
        concept[IDENTIFIER] = name
        return True

    if prefix == 'bel' and KIND in node:
        kind = node[KIND]
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
        return True

    if prefix == 'uniprot':
        # assume identifier given as name
        identifier = get_id_from_mnemonic(name)
        if identifier is not None:
            concept[IDENTIFIER] = identifier
            return True

        mnemomic = get_mnemonic(name, web_fallback=True)
        if mnemomic is not None:
            concept[IDENTIFIER] = name
            concept[NAME] = mnemomic
            return True

        logger.warning('could not interpret uniprot name: %s', name)
        return False

    try:
        id_name_mapping = get_name_id_mapping(prefix)
    except NoOboFoundry:
        id_name_mapping = None

    if id_name_mapping is None:
        logger.warning('unhandled namespace in %s ! %s', prefix, name)
        return False

    identifier = id_name_mapping.get(name)
    if identifier is None:
        logger.warning('could not find name %s in namespace %s', name, prefix)
        return False

    concept[IDENTIFIER] = identifier
    return True


def _process_fusion(fusion) -> bool:
    success_3p = _process_node(fusion[PARTNER_3P])
    success_5p = _process_node(fusion[PARTNER_5P])
    return success_3p and success_5p


def _process_list(members) -> bool:
    success = True
    for member in members:
        success = success and _process_node(member)
    return success


class TestGround(unittest.TestCase):
    """Test grounding."""

    def test_process_concept(self):
        """Test several cases in processing concepts."""
        r = [
            (
                'Normalize prefix to correct case',
                {CONCEPT: {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'}},
                {CONCEPT: {NAMESPACE: 'MESH', NAME: 'Neurons', IDENTIFIER: 'D009474'}},
            ),
            (
                'Normalize prefix by synonym',
                {CONCEPT: {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'}},
                {CONCEPT: {NAMESPACE: 'MESHA', NAME: 'Neurons', IDENTIFIER: 'D009474'}},
            ),
            (
                'Look up identifier by name',
                {CONCEPT: {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'}},
                {CONCEPT: {NAMESPACE: 'MESH', NAME: 'Neurons'}},
            ),
            (
                'Lookup by UniProt identifier as name',
                {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'}},
                {CONCEPT: {NAMESPACE: 'UniProt', NAME: 'O60921'}},
            ),
            (
                'Lookup by UniProt mnemonic as name',
                {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'}},
                {CONCEPT: {NAMESPACE: 'UniProt', NAME: 'HUS1_HUMAN'}},
            ),
            (
                'Rewrite wrong UniProt name',
                {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'}},
                {CONCEPT: {NAMESPACE: 'UniProt', NAME: 'WRONG!!!!', IDENTIFIER: 'O60921'}},
            ),
            (
                'Overwrite name by identifier',
                {CONCEPT: {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'}},
                {CONCEPT: {NAMESPACE: 'MESH', NAME: 'Nonsense name!', IDENTIFIER: 'D009474'}},
            ),
            (
                'Remap example 1',
                {CONCEPT: {NAMESPACE: 'fplx', NAME: 'TAP', IDENTIFIER: 'TAP'}},
                {CONCEPT: {NAMESPACE: 'SFAM', NAME: 'TAP Family'}},
            ),
            (
                'Remap example 2',
                {CONCEPT: {NAMESPACE: 'fplx', NAME: 'Gamma_secretase', IDENTIFIER: 'Gamma_secretase'}},
                {CONCEPT: {NAMESPACE: 'SCOMP', NAME: 'gamma Secretase Complex'}},
            ),
        ]
        for name, expected, result in r:
            with self.subTest(name=name):
                self.assertIn(expected[CONCEPT][NAMESPACE], SYNONYM_TO_KEY)
                _process_concept(node=result)
                self.assertEqual(expected, result)

    def test_process_nodes(self):
        """Test several cases dealing with full nodes."""
        r = [
            (
                'Look up identifier of member by name',
                {MEMBERS: [{CONCEPT: {NAMESPACE: 'mesh', NAME: 'Neurons', IDENTIFIER: 'D009474'}}]},
                {MEMBERS: [{CONCEPT: {NAMESPACE: 'MESH', NAME: 'Neurons'}}]},
            ),
            (
                'Look up identifier of member by name AND name of complex',
                {
                    CONCEPT: {NAMESPACE: 'complexportal', NAME: 'Checkpoint clamp complex', IDENTIFIER: 'CPX-1829'},
                    MEMBERS: [
                        {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'}},
                        {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'RAD9A_HUMAN', IDENTIFIER: 'Q99638'}},
                        {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'RAD1_HUMAN', IDENTIFIER: 'O60671'}},
                    ]
                },
                {
                    CONCEPT: {NAMESPACE: 'complexportal', NAME: 'Checkpoint clamp complex'},
                    MEMBERS: [
                        {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN'}},
                        {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'RAD9A_HUMAN'}},
                        {CONCEPT: {NAMESPACE: 'uniprot', NAME: 'RAD1_HUMAN'}},
                    ]
                },
            ),
            (
                'Normalize pmod by name',
                {
                    CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
                    VARIANTS: [
                        {
                            KIND: PMOD,
                            CONCEPT: {NAMESPACE: 'go', IDENTIFIER: '0006468', NAME: 'protein phosphorylation'},
                        },
                    ]
                },
                {
                    CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN'},
                    VARIANTS: [
                        {
                            KIND: PMOD,
                            CONCEPT: {NAMESPACE: 'GO', NAME: 'protein phosphorylation'},
                        },
                    ]
                },
            ),
            (
                'Fix name in pmod by identifier lookup',
                {
                    CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
                    VARIANTS: [
                        {
                            KIND: PMOD,
                            CONCEPT: {NAMESPACE: 'go', IDENTIFIER: '0006468', NAME: 'protein phosphorylation'},
                        },
                    ]
                },
                {
                    CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN'},
                    VARIANTS: [
                        {
                            KIND: PMOD,
                            CONCEPT: {NAMESPACE: 'GO', IDENTIFIER: '0006468', NAME: 'WRONG!'},
                        },
                    ]
                },
            ),
            (
                'Normalize pmod using default BEL namespace',
                {
                    CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
                    VARIANTS: [
                        {
                            KIND: PMOD,
                            CONCEPT: {NAMESPACE: 'go', IDENTIFIER: '0006468', NAME: 'protein phosphorylation'},
                        },
                    ]
                },
                {
                    CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN'},
                    VARIANTS: [
                        {
                            KIND: PMOD,
                            CONCEPT: {NAMESPACE: 'bel', NAME: 'Ph'},
                        },
                    ]
                },
            ),
            (
                'Normalize pmod using default BEL namespace - Me (to investigate conflict with gmod)',
                {
                    CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN', IDENTIFIER: 'O60921'},
                    VARIANTS: [
                        {
                            KIND: PMOD,
                            CONCEPT: {NAMESPACE: 'go', IDENTIFIER: '0006479', NAME: 'protein methylation'}
                        },
                    ]
                },
                {
                    CONCEPT: {NAMESPACE: 'uniprot', NAME: 'HUS1_HUMAN'},
                    VARIANTS: [
                        {
                            KIND: PMOD,
                            CONCEPT: {NAMESPACE: 'bel', NAME: 'Me'}
                        },
                    ]
                },
            ),
            (
                'Normalize gmod using default BEL namespace - Me (to investigate conflict with pmod)',
                {
                    CONCEPT: {NAMESPACE: 'hgnc', NAME: 'MAPT', IDENTIFIER: '6893'},
                    VARIANTS: [
                        {CONCEPT: {NAMESPACE: 'go', IDENTIFIER: '0006306', NAME: 'DNA methylation'}, KIND: GMOD},
                    ]
                },
                {
                    CONCEPT: {NAMESPACE: 'HGNC', NAME: 'MAPT'},
                    VARIANTS: [
                        {CONCEPT: {NAMESPACE: 'bel', NAME: 'Me'}, KIND: GMOD},
                    ]
                },
            ),
        ]
        for name, expected, result in r:
            with self.subTest(name=name):
                _process_node(result)
                self.assertEqual(expected, result)

# TODO look up members when checking a named complex, protein family, or pathway
