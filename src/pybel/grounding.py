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
from collections import defaultdict
from typing import Any, Mapping, Tuple, Union

from protmapper.uniprot_client import get_id_from_mnemonic, get_mnemonic
from pyobo.extract import get_id_name_mapping, get_name_id_mapping
from pyobo.getters import NoOboFoundry
from pyobo.identifier_utils import SYNONYM_TO_KEY, normalize_prefix
from pyobo.xrefdb.sources.famplex import get_remapping
from tqdm import tqdm

from pybel.constants import (
    ACTIVITY, ANNOTATIONS, CONCEPT, EFFECT, FROM_LOC, FUSION, GMOD, IDENTIFIER, KIND, LOCATION, MEMBERS, MODIFIER, NAME,
    NAMESPACE, OBJECT, PARTNER_3P, PARTNER_5P, PMOD, PRODUCTS, REACTANTS, SUBJECT, TO_LOC, TRANSLOCATION, VARIANTS,
)
from pybel.io import from_nodelink, to_nodelink
from pybel.language import Entity, activity_mapping, compartment_mapping, gmod_mappings, pmod_mappings
from pybel.struct import BELGraph, get_annotations, get_namespaces, get_ungrounded_nodes

__all__ = [
    'ground',
    'ground_nodelink',
]

logger = logging.getLogger(__name__)
SKIP = {'ncbigene', 'pubchem.compound'}
NO_NAMES = {'fplx', 'eccode', 'dbsnp'}

# TODO will get updated
#: A mapping of (prefix, name) pairs to (prefix, identifier, name) triples
_NAME_REMAPPING = get_remapping()

#: A mapping of (prefix, identifier) pairs to (prefix, identifier, name) triples
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

    remove_unused_annotation_metadata(graph)

    if remove_ungrounded:
        ungrounded_nodes = get_ungrounded_nodes(graph)
        graph.remove_nodes_from(ungrounded_nodes)
        graph.namespace_url.clear()
        graph.namespace_pattern.clear()
        graph.namespace_pattern.update({
            namespace: '.*'
            for namespace in get_namespaces(graph)
        })

        graph.annotation_url.clear()
        graph.annotation_pattern.clear()
        graph.annotation_list.clear()
        graph.annotation_pattern.update({
            annotation: '.*'
            for annotation in get_annotations(graph)
        })

    return graph


def remove_unused_annotation_metadata(graph) -> None:
    used_annotations = get_annotations(graph)

    unused_patterns = set(graph.annotation_pattern) - used_annotations
    for annotation in unused_patterns:
        logger.warning('deleting unused annotation pattern: %s', annotation)
        del graph.annotation_pattern[annotation]

    unused_urls = set(graph.annotation_pattern) - used_annotations
    for annotation in unused_urls:
        logger.warning('deleting unused annotation URL: %s', annotation)
        del graph.annotation_url[annotation]

    unused_lists = set(graph.annotation_list) - used_annotations
    for annotation in unused_lists:
        logger.warning('deleting unused annotation list: %s', annotation)
        del graph.annotation_list[annotation]


def ground_nodelink(graph_nodelink_dict) -> None:
    """Ground entities in a nodelink data structure."""
    name = graph_nodelink_dict.get('graph', {}).get('name', 'graph')

    for data in tqdm(graph_nodelink_dict['links'], desc='grounding edges in {}'.format(name)):
        _process_edge_side(data.get(SUBJECT))
        _process_edge_side(data.get(OBJECT))
        if ANNOTATIONS in data:
            _process_annotations(data)

    for node in tqdm(graph_nodelink_dict['nodes'], desc='grounding nodes in {}'.format(name)):
        _process_node(node)


_BEL_ANNOTATION_PREFIX_MAP = {
    'MeSHDisease': 'mesh',
    'MeSHAnatomy': 'mesh',
    'Species': 'ncbitaxon',
    'Disease': 'doid',
    'Cell': 'cl',
}
_UNHANDLED_ANNOTATION = set()


def _process_annotations(data, add_free_annotations: bool = False):
    x = []
    y = []
    for prefix, names in data[ANNOTATIONS].items():
        if prefix == 'CellLine':
            efo_name_to_id = get_name_id_mapping('efo')
            # clo_name_to_id = get_name_id_mapping('clo')  # FIXME implement CLO import
            for name, polarity in names.items():
                prefix, identifier = 'efo', efo_name_to_id.get(name)
                # if identifier is None:
                #     prefix, identifier = 'clo', clo_name_to_id.get(name)
                if identifier is not None:
                    x.append((Entity(namespace=prefix, identifier=identifier, name=name), polarity))
                else:
                    y.append((prefix, identifier, polarity))
        elif prefix in _BEL_ANNOTATION_PREFIX_MAP:
            prefix = _BEL_ANNOTATION_PREFIX_MAP[prefix]
            name_id = get_name_id_mapping(prefix)
            for name, polarity in names.items():
                identifier = name_id.get(name)
                if identifier:
                    x.append((Entity(namespace=prefix, identifier=identifier, name=name), polarity))
                else:
                    y.append((prefix, name, polarity))
        else:
            if prefix not in _UNHANDLED_ANNOTATION:
                logger.warning('unhandled annotation: %s', prefix)
                _UNHANDLED_ANNOTATION.add(prefix)
            for name, polarity in names.items():
                y.append((prefix, name, polarity))

    data[ANNOTATIONS] = defaultdict(dict)
    for entity, polarity in x:
        data[ANNOTATIONS][entity.namespace][entity.identifier] = polarity

    if add_free_annotations:
        data['free_annotations'] = defaultdict(dict)
        for prefix, name, polarity in y:
            data['free_annotations'][prefix][name] = polarity


def _process_edge_side(side_data) -> bool:
    """Process an edge JSON object, in place."""
    if side_data is None:
        return True

    modifier = side_data.get(MODIFIER)
    effect = side_data.get(EFFECT)

    if modifier == ACTIVITY and effect is not None:
        _process_concept(concept=effect)
    elif modifier == TRANSLOCATION and effect is not None:
        _process_concept(concept=effect[FROM_LOC])
        _process_concept(concept=effect[TO_LOC])

    location = side_data.get(LOCATION)
    if location is not None:
        _process_concept(concept=location)


_UNHANDLED_NAMESPACES = set()


def _process_node(node: Mapping[str, Any]) -> bool:
    """Process a node JSON object, in place.

    :return: If all parts of the node were successfully grounded
    """
    success = True
    if CONCEPT in node:
        success = success and _process_concept(concept=node[CONCEPT], node=node)
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


def _process_concept(*, concept, node=None) -> bool:
    """Process a node JSON object."""
    namespace = concept[NAMESPACE]
    if namespace.lower() in {'text', 'fixme'}:
        return False

    prefix = normalize_prefix(namespace)
    if prefix is None:
        logger.warning('could not normalize namespace: %s ! %s', namespace, concept.name)
        return False

    concept[NAMESPACE] = prefix

    identifier = concept.get(IDENTIFIER)
    name = concept.get(NAME)
    if identifier:  # don't trust whatever was put for the name, even if it's available
        map_success = _handle_identifier_not_name(concept=concept, prefix=prefix, identifier=identifier)
    else:
        map_success = _handle_name_and_not_identifier(concept=concept, prefix=prefix, name=name, node=node)

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
    if prefix in NO_NAMES:
        concept[NAME] = concept[IDENTIFIER]
        return True

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


def _handle_name_and_not_identifier(*, concept, prefix, name, node=None) -> bool:
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

    if prefix == 'bel' and node is not None and KIND in node:
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
    elif prefix == 'bel' and name in activity_mapping:
        _mapped = activity_mapping[name]
        concept[NAMESPACE] = _mapped[NAMESPACE]
        concept[IDENTIFIER] = _mapped[IDENTIFIER]
        concept[NAME] = _mapped[NAME]
        return True
    elif prefix == 'bel' and name in compartment_mapping:
        _mapped = compartment_mapping[name]
        concept[NAMESPACE] = _mapped[NAMESPACE]
        concept[IDENTIFIER] = _mapped[IDENTIFIER]
        concept[NAME] = _mapped[NAME]
        return True
    elif prefix == 'bel':
        logger.warning('could not figure out how to map bel ! %s', name)
        return False

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
                _process_concept(concept=result[CONCEPT], node=result)
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
