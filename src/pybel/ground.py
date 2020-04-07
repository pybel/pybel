"""Grounding BEL JSON."""

import pyobo
from tqdm import tqdm

import pybel
from pybel import BELGraph
from pybel.constants import (
    CONCEPT, FUSION, IDENTIFIER, MEMBERS, NAME, NAMESPACE, PARTNER_3P, PARTNER_5P, PRODUCTS,
    REACTANTS,
)

__all__ = [
    'ground_nodelink',
    'ground_graph',
]

NO_NAMES = {'fplx', 'eccode'}


def ground_graph(graph: BELGraph) -> BELGraph:
    """Ground all entities in a BEL graph."""
    j = pybel.to_nodelink(graph)
    ground_nodelink(j)
    return pybel.from_nodelink(j)


def ground_nodelink(j) -> None:
    """Ground entities in a nodelink data structure."""
    name_to_ids = {
        prefix: pyobo.get_name_id_mapping(prefix)
        for prefix in ('hgnc', 'chebi', 'mgi', 'rgd', 'go', 'mesh', 'hgnc.genefamily')
    }

    for node in tqdm(j['nodes'], desc='mapping nodes'):
        _process_concept(node, name_to_ids)
        _process_members(node, name_to_ids, MEMBERS)
        _process_members(node, name_to_ids, REACTANTS)
        _process_members(node, name_to_ids, PRODUCTS)
        _process_fusion(node, name_to_ids)


def _process_concept(node, name_to_ids):
    concept = node.get(CONCEPT)
    if concept is None:
        return

    namespace = concept[NAMESPACE] = concept[NAMESPACE].lower()
    if namespace in NO_NAMES:
        concept[IDENTIFIER] = concept[NAME]
    elif namespace in name_to_ids:
        identifier = name_to_ids[namespace].get(concept[NAME])
        if identifier is not None:
            concept[IDENTIFIER] = identifier


def _process_fusion(node, name_to_ids):
    fusion = node.get(FUSION)
    if not fusion:
        return
    _process_concept(fusion[PARTNER_3P], name_to_ids)
    _process_concept(fusion[PARTNER_5P], name_to_ids)


def _process_members(node, name_to_ids, key):
    members = node.get(key)
    if not members:
        return
    for member in members:
        _process_concept(member, name_to_ids)
