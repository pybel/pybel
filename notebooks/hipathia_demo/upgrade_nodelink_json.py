import json
import os

import pyobo
from tqdm import tqdm

HERE = os.path.dirname(__file__)
IN = os.path.join(HERE, 'alzheimers.bel.nodelink.json')
OUT = os.path.join(HERE, 'alzheimers_grounded.bel.nodelink.json')

NO_NAMES = {'fplx', 'eccode'}


def upgrade():
    name_to_ids = {
        prefix: pyobo.get_name_id_mapping(prefix)
        for prefix in ('hgnc', 'chebi', 'mgi', 'rgd', 'go', 'mesh', 'hgnc.genefamily')
    }

    with open(IN) as file:
        j = json.load(file)

    for node in tqdm(j['nodes'], desc='mapping nodes'):
        _process_concept(node, name_to_ids)
        _process_members(node, name_to_ids, 'members')
        _process_members(node, name_to_ids, 'reactants')
        _process_members(node, name_to_ids, 'products')

    with open(OUT, 'w') as file:
        json.dump(j, file, indent=2)


def _process_concept(node, name_to_ids):
    concept = node.get('concept')
    if concept is None:
        return
    namespace = concept['namespace'].lower()

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


if __name__ == '__main__':
    upgrade()
