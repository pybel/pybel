# -*- coding: utf-8 -*-

"""Convert parsed SBGN-ML to BEL."""

import json
import uuid
from typing import Any, List, Mapping, Optional

from pybel import BELGraph, dsl

__all__ = [
    'convert_sbgn',
    'convert_file',
]

DSL_MAPPING = {
    'simple molecule': dsl.Abundance,
    'macromolecule': dsl.Protein,
    'nucleic acid feature': dsl.Rna,
}


def convert_file(path: str) -> BELGraph:
    with open(path) as file:
        j = json.load(file)
    return convert_sbgn(j)


def convert_sbgn(j: Mapping[str, Any]) -> BELGraph:
    """Convert a JSON dictionary."""
    title = j.get('title', str(uuid.uuid4()))
    graph = BELGraph(name=title)

    for reified_edge in j.get('reified', []):
        _handle_reified_edge(graph, reified_edge)

    for direct_edge in j.get('direct', []):
        _handle_direct_edge(graph, direct_edge)

    return graph


def _handle_reified_edge(graph: BELGraph, d: Mapping[str, Any]) -> None:
    cls = d['process']
    sources = d.get('sources', {})
    source_consumption: List = sources.get('consumption', [])
    target_production: List = d.get('targets', {}).get('production', [])

    catalysts = []
    for catalyst in sources.get('catalysis', []):
        b = _convert_refied_to_bel(catalyst)
        if b:
            catalysts.append(b)

    inhibitors = []
    for inhibitor in sources.get('inhibition', []):
        b = _convert_refied_to_bel(inhibitor)
        if b:
            inhibitors.append(b)

    sources = [_convert_refied_to_bel(x) for x in source_consumption]

    targets = [_convert_refied_to_bel(x) for x in target_production]

    if source_consumption and target_production:
        if any(z is None for z in sources) or any(z is None for z in targets):
            return

        # Complex formation
        if (
            len(targets) == 1
            and isinstance(targets[0], dsl.ComplexAbundance)
            and all(r in targets[0].members for r in sources)
        ):
            compl = targets[0]
            graph.add_node_from_data(compl)
            for catalyst in catalysts:
                graph.add_increases(catalyst, compl, citation='', evidence='')
            for inhibitor in inhibitors:
                graph.add_decreases(inhibitor, compl, citation='', evidence='')
            return

        print('## UNHANDLED RXN', '\n  ', sources, '\n  ', cls, '\n  ', targets)


def _convert_refied_to_bel(x) -> dsl.BaseAbundance:
    glyph = x['glyph']
    return _glyph_to_bel(glyph)


def _handle_direct_edge(graph: BELGraph, d: Mapping[str, Any]) -> Optional[str]:
    edge_type = d['arc_class']
    source = d['source']
    source_bel = _glyph_to_bel(source)
    target = d['target']
    target_bel = _glyph_to_bel(target)
    if not source_bel or not target_bel:
        return

    if edge_type in {'inhibition'}:
        return graph.add_inhibits(
            source_bel, target_bel,
            citation='', evidence='', annotations={'sbgnml_edge': edge_type},
        )
    if edge_type in {'stimulation', 'necessary stimulation'}:
        return graph.add_activates(
            source_bel, target_bel,
            citation='', evidence='', annotations={'sbgnml_edge': edge_type},
        )

    print('##', source_bel, edge_type, target_bel)


def _glyph_to_bel(glyph):
    """Convert an entity to BEL."""
    cls = glyph['class']
    entity = glyph.get('entity')
    components = glyph.get('components')

    if cls == 'macromolecule' and entity and entity['prefix'] and entity['identifier']:
        rv = dsl.Protein(
            namespace=entity['prefix'],
            identifier=entity['identifier'],
            name=entity['name'],
        )
        # print('found protein', rv)
        return rv

    elif cls == 'phenotype' and entity and entity['identifier']:
        rv = dsl.BiologicalProcess(
            namespace=entity['prefix'],
            identifier=entity['identifier'],
            name=entity['name'],
        )
        # print('found BP', rv)
        return rv

    elif cls == 'simple chemical' and entity and entity['prefix'] == 'chebi':
        rv = dsl.Abundance(
            namespace=entity['prefix'],
            identifier=entity['identifier'],
            name=entity['name'],
        )
        # print('found chemical', rv)
        return rv
    elif cls == 'complex' and components:
        if len(components) == 1:
            c = list(components.values())[0]
            if not c['entity']['identifier']:
                print('unhandled complex of ', components)
                return
            return dsl.NamedComplexAbundance(
                namespace=c['entity']['prefix'],
                identifier=c['entity']['identifier'],
                name=c['entity']['name'],
            )
        elif all(c['entity']['prefix'] for c in components.values()):
            rv = dsl.ComplexAbundance([
                dsl.Protein(
                    namespace=c['entity']['prefix'],
                    identifier=c['entity']['identifier'],
                    name=c['entity']['name'],
                )
                for c in components.values()
            ])
            return rv
        else:
            print('unhandled complex of', components)

        return
    elif cls == 'nucleic acid feature' and entity and entity['prefix']:
        rv = dsl.Rna(
            namespace=entity['prefix'],
            identifier=entity['identifier'],
            name=entity['name'],
        )
        return rv

    print('unhandled', glyph)
