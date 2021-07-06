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
from typing import Any, Collection, Mapping, Optional, Tuple, Union

import pyobo
from protmapper.uniprot_client import get_id_from_mnemonic, get_mnemonic
from pyobo.getters import NoBuild
from pyobo.identifier_utils import normalize_prefix
from pyobo.xrefdb.sources.famplex import get_remapping
from tqdm.autonotebook import tqdm

from pybel.constants import (
    ACTIVITY, ANNOTATIONS, CONCEPT, EFFECT, FROM_LOC, FUSION, GMOD, IDENTIFIER, KIND, LOCATION,
    MEMBERS, MODIFIER, NAME, NAMESPACE, PARTNER_3P, PARTNER_5P, PMOD, PRODUCTS, REACTANTS, SOURCE_MODIFIER,
    TARGET_MODIFIER, TO_LOC, TRANSLOCATION, VARIANTS,
)
from pybel.dsl import BaseConcept
from pybel.io import from_nodelink, to_nodelink
from pybel.language import (
    Entity, activity_mapping, compartment_mapping, gmod_mappings, pmod_mappings, text_location_labels,
)
from pybel.struct import BELGraph, get_annotations, get_namespaces, get_ungrounded_nodes

__all__ = [
    'ground',
    'ground_nodelink',
]

logger = logging.getLogger(__name__)
SKIP = {'ncbigene', 'pubchem.compound', 'chembl.compound'}
NO_NAMES = {'fplx', 'eccode', 'dbsnp', 'smiles', 'inchi', 'inchikey'}

# TODO will get updated
#: A mapping of (prefix, name) pairs to (prefix, identifier, name) triples
_NAME_REMAPPING = get_remapping()

#: A mapping of (prefix, identifier) pairs to (prefix, identifier, name) triples
_ID_REMAPPING = {}


def _get_name_remapping(prefix: str, name: str) -> Union[Tuple[str, str, str], Tuple[None, None, None]]:
    return _NAME_REMAPPING.get((prefix, name), (None, None, None))


def _get_id_remapping(prefix: str, identifier: str) -> Union[Tuple[str, str, str], Tuple[None, None, None]]:
    return _ID_REMAPPING.get((prefix, identifier), (None, None, None))


def ground(
    graph: BELGraph,
    remove_ungrounded: bool = True,
    skip_namespaces: Optional[Collection[str]] = None,
) -> BELGraph:
    """Ground all entities in a BEL graph."""
    j = to_nodelink(graph)
    ground_nodelink(j, skip_namespaces=skip_namespaces)
    graph = from_nodelink(j)

    remove_unused_annotation_metadata(graph)

    if remove_ungrounded:
        ungrounded_nodes = {
            node
            for node in get_ungrounded_nodes(graph)
            if not isinstance(node, BaseConcept) or node.namespace not in NO_NAMES
        }
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


def ground_nodelink(graph_nodelink_dict, skip_namespaces: Optional[Collection[str]] = None) -> None:
    """Ground entities in a nodelink data structure."""
    name = graph_nodelink_dict.get('graph', {}).get('name', 'graph')

    for data in tqdm(graph_nodelink_dict['links'], desc='grounding edges in {}'.format(name)):
        _process_edge_side(data.get(SOURCE_MODIFIER), skip_namespaces=skip_namespaces)
        _process_edge_side(data.get(TARGET_MODIFIER), skip_namespaces=skip_namespaces)
        if ANNOTATIONS in data:
            _process_annotations(data, skip_namespaces=skip_namespaces)

    for node in tqdm(graph_nodelink_dict['nodes'], desc='grounding nodes in {}'.format(name)):
        _process_node(node, skip_namespaces=skip_namespaces)


_BEL_ANNOTATION_PREFIX_MAP = {
    'MeSHDisease': 'mesh',
    'MeSHAnatomy': 'mesh',
    'CellStructure': 'mesh',
    'Species': 'ncbitaxon',
    'Disease': 'doid',
    'Cell': 'cl',
    'Anatomy': 'uberon',
}
_BEL_ANNOTATION_PREFIX_CATEGORY_MAP = {
    'MeSHDisease': 'Disease',
    'MeSHAnatomy': 'Anatomy',
}

_UNHANDLED_ANNOTATION = set()
CATEGORY_BLACKLIST = {
    'TextLocation',
}


def _process_annotations(
    data,
    remove_ungrounded: bool = False,
    skip_namespaces: Optional[Collection[str]] = None,
) -> None:
    """Process the annotations in a PyBEL edge data dictionary."""
    cell_line_entities = data[ANNOTATIONS].get('CellLine')
    if cell_line_entities:
        ne = []
        for entity in cell_line_entities:
            if entity[NAMESPACE] == 'CellLine':
                _namespaces = [
                    'efo',
                    # 'clo',  # FIXME implement CLO in PyOBO then uncomment
                ]
                g_prefix, g_identifier, g_name = pyobo.ground(_namespaces, entity[IDENTIFIER])
                if g_prefix and g_identifier:
                    ne.append(Entity(namespace=g_prefix, identifier=g_identifier, name=g_name))
                elif not remove_ungrounded:
                    logger.warning('could not ground CellLine: "%s"', entity[IDENTIFIER])
                    ne.append(entity)
        data[ANNOTATIONS]['CellLine'] = ne

    # fix text locations
    text_location = data[ANNOTATIONS].get('TextLocation')
    if text_location:
        data[ANNOTATIONS]['TextLocation'] = [
            text_location_labels.get(entity.identifier, entity)
            for entity in text_location
        ]

    # remap category names
    data[ANNOTATIONS] = {
        _BEL_ANNOTATION_PREFIX_CATEGORY_MAP.get(category, category): entities
        for category, entities in data[ANNOTATIONS].items()
    }
    # fix namespaces that were categories before
    for category, entities in data[ANNOTATIONS].items():
        if category in CATEGORY_BLACKLIST:
            continue

        ne = []
        for entity in entities:
            if not isinstance(entity, dict):
                raise TypeError(f'entity should be a dict. got: {entity}')
            nn = _BEL_ANNOTATION_PREFIX_MAP.get(entity[NAMESPACE])
            if nn is not None:
                entity[NAMESPACE] = nn

            _process_concept(concept=entity, skip_namespaces=skip_namespaces)
            ne.append(entity)
        data[ANNOTATIONS][category] = ne


def _process_edge_side(side_data, skip_namespaces: Optional[Collection[str]] = None) -> bool:
    """Process an edge JSON object, in place."""
    if side_data is None:
        return True

    modifier = side_data.get(MODIFIER)
    effect = side_data.get(EFFECT)

    if modifier == ACTIVITY and effect is not None:
        _process_concept(concept=effect, skip_namespaces=skip_namespaces)
    elif modifier == TRANSLOCATION and effect is not None:
        _process_concept(concept=effect[FROM_LOC], skip_namespaces=skip_namespaces)
        _process_concept(concept=effect[TO_LOC], skip_namespaces=skip_namespaces)

    location = side_data.get(LOCATION)
    if location is not None:
        _process_concept(concept=location, skip_namespaces=skip_namespaces)


_UNHANDLED_NAMESPACES = set()


def _process_node(node: Mapping[str, Any], skip_namespaces: Optional[Collection[str]] = None) -> bool:
    """Process a node JSON object, in place.

    :return: If all parts of the node were successfully grounded
    """
    success = True
    if CONCEPT in node:
        success = success and _process_concept(concept=node[CONCEPT], node=node, skip_namespaces=skip_namespaces)
    if VARIANTS in node:
        success = success and _process_list(node[VARIANTS], skip_namespaces=skip_namespaces)
    if MEMBERS in node:
        success = success and _process_list(node[MEMBERS], skip_namespaces=skip_namespaces)
    if REACTANTS in node:
        success = success and _process_list(node[REACTANTS], skip_namespaces=skip_namespaces)
    if PRODUCTS in node:
        success = success and _process_list(node[PRODUCTS], skip_namespaces=skip_namespaces)
    if FUSION in node:
        success = success and _process_fusion(node[FUSION], skip_namespaces=skip_namespaces)
    return success


def _process_concept(*, concept, node=None, skip_namespaces: Optional[Collection[str]] = None) -> bool:
    """Process a node JSON object."""
    namespace = concept[NAMESPACE]
    if namespace.lower() in {'text', 'fixme'}:
        return False

    if skip_namespaces and namespace in skip_namespaces:
        return True

    prefix = normalize_prefix(namespace)
    if prefix is None:
        logger.warning('could not normalize namespace "%s" in concept "%s"', namespace, concept)
        return False

    concept[NAMESPACE] = prefix

    identifier = concept.get(IDENTIFIER)
    name = concept.get(NAME)
    if identifier:  # don't trust whatever was put for the name, even if it's available
        map_success = _handle_identifier_not_name(
            concept=concept,
            prefix=prefix,
            identifier=identifier,
            skip_namespaces=skip_namespaces
        )
        if not map_success:  # just in case the name gets put in the identifier
            map_success = _handle_name_and_not_identifier(
                concept=concept, prefix=prefix, name=identifier, node=node,
                skip_namespaces=skip_namespaces,
            )
    else:
        map_success = _handle_name_and_not_identifier(
            concept=concept, prefix=prefix, name=name, node=node,
            skip_namespaces=skip_namespaces,
        )

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


def _handle_identifier_not_name(
    *, concept, prefix, identifier, skip_namespaces: Optional[Collection[str]] = None,
) -> bool:
    # Some namespaces are just too much of a problem at the moment to look up
    if prefix in SKIP:
        return False
    if skip_namespaces and prefix in skip_namespaces:
        return True

    if prefix in NO_NAMES:
        concept[NAME] = concept[IDENTIFIER]
        return True

    if prefix == 'uniprot':
        concept[NAME] = get_mnemonic(identifier)
        return True

    try:
        id_name_mapping = pyobo.api.names.get_id_name_mapping(prefix)
    except NoBuild:
        return False

    if id_name_mapping is None:
        logger.warning('could not get names for prefix "%s"', prefix)
        return False

    name = id_name_mapping.get(identifier)
    if name is None:
        logger.warning('could not get name for curie %s:%s', prefix, identifier)
        return False
    concept[NAME] = name

    return True


def _handle_name_and_not_identifier(
    *, concept, prefix, name, node=None, skip_namespaces: Optional[Collection[str]] = None,
) -> bool:
    remapped_prefix, remapped_identifier, remapped_name = _get_name_remapping(prefix, name)
    if remapped_prefix:
        concept[NAMESPACE] = remapped_prefix
        concept[IDENTIFIER] = remapped_identifier
        concept[NAME] = remapped_name
        return True

    # Some namespaces are just too much of a problem at the moment to look up
    if prefix in SKIP:
        return False
    if skip_namespaces and prefix in skip_namespaces:
        return True

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
        logger.warning('could not figure out how to map bel ! "%s"', name)
        return False

    if prefix == 'uniprot':
        # assume identifier given as name
        identifier = get_id_from_mnemonic(name)
        if identifier is not None:
            concept[IDENTIFIER] = identifier
            return True

        mnemomic = get_mnemonic(name, web_fallback=False)
        if mnemomic is not None:
            concept[IDENTIFIER] = name
            concept[NAME] = mnemomic
            return True

        logger.warning('could not interpret uniprot name: "%s"', name)
        return False

    try:
        id_name_mapping = pyobo.api.names.get_name_id_mapping(prefix)
    except NoBuild as e:
        logger.warning('could not get namespace %s - %s', prefix, e)
        return False

    if id_name_mapping is None:
        logger.warning('unhandled namespace in %s ! %s', prefix, name)
        return False

    identifier = id_name_mapping.get(name)
    if identifier is None:
        logger.warning('could not find name "%s" in namespace "%s"', name, prefix)
        return False

    concept[IDENTIFIER] = identifier
    concept[NAME] = name
    return True


def _process_fusion(fusion, skip_namespaces: Optional[Collection[str]] = None) -> bool:
    success_3p = _process_node(fusion[PARTNER_3P], skip_namespaces=skip_namespaces)
    success_5p = _process_node(fusion[PARTNER_5P], skip_namespaces=skip_namespaces)
    return success_3p and success_5p


def _process_list(members, skip_namespaces: Optional[Collection[str]] = None) -> bool:
    success = True
    for member in members:
        success = success and _process_node(member, skip_namespaces=skip_namespaces)
    return success
