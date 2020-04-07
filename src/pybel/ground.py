"""Grounding BEL JSON."""

import pyobo
from tqdm import tqdm

import pybel
from pybel import BELGraph

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
        _process_members(node, name_to_ids, 'members')
        _process_members(node, name_to_ids, 'reactants')
        _process_members(node, name_to_ids, 'products')


def _process_concept(node, name_to_ids):
    concept = node.get('concept')
    if concept is None:
        return

    namespace = concept['namespace'] = concept['namespace'].lower()
    if namespace in NO_NAMES:
        concept['identifier'] = concept['name']
    elif namespace in name_to_ids:
        identifier = name_to_ids[namespace].get(concept['name'])
        if identifier is not None:
            concept['identifier'] = identifier


def _process_members(node, name_to_ids, key):
    members = node.get(key)
    if not members:
        return
    for member in members:
        _process_concept(member, name_to_ids)
