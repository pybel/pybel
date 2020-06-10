# -*- coding: utf-8 -*-

"""Convert parsed SBGN-ML to BEL."""

import json
import logging
import uuid
from typing import Any, List, Mapping, Optional

from pybel import BELGraph, dsl
from pybel.dsl import CentralDogma

__all__ = [
    'convert_sbgn',
    'convert_file',
]

logger = logging.getLogger(__name__)


def convert_file(path: str) -> BELGraph:
    """Convert a SBGN-ML file."""
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
    t_sources = d.get('sources', {})
    source_consumption: List = t_sources.get('consumption', [])
    target_production: List = d.get('targets', {}).get('production', [])

    catalysts = []
    for catalyst in t_sources.get('catalysis', []):
        b = _convert_refied_to_bel(catalyst)
        if b:
            catalysts.append(b)

    inhibitors = []
    for inhibitor in t_sources.get('inhibition', []):
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
        if (
            len(sources) == 1 and len(targets) == 1
            and isinstance(sources[0], CentralDogma)
            and isinstance(targets[0], CentralDogma)
            and sources[0].entity == targets[0].entity
        ):  # either forward or backward pmod
            source = sources[0]
            target = targets[0]
            if source.variants and not target.variants:  # backward pmod (removal)
                if not catalysts and not inhibitors:
                    print('free backward pmod statement')
                    graph.add_node_from_data(source)
                for catalyst in catalysts:
                    graph.add_decreases(catalyst, source, citation='', evidence='')
                for inhibitor in inhibitors:
                    graph.add_increases(inhibitor, source, citation='', evidence='')
                return
            elif not source.variants and not target.variants:  # forward mod
                if not catalysts and not inhibitors:
                    print('free pmod statement')
                    graph.add_node_from_data(target)
                for catalyst in catalysts:
                    graph.add_increases(catalyst, source, citation='', evidence='')
                for inhibitor in inhibitors:
                    graph.add_decreases(inhibitor, source, citation='', evidence='')
                return
            elif source.variants and target.variants:
                print('@@unhandled complex pmod statement')
            else:
                pass

        print('## UNHANDLED RXN', '\n  ', sources, '\n  ', cls, '\n  ', targets, '\n   Source keys:', t_sources.keys())


def _convert_refied_to_bel(x) -> dsl.BaseAbundance:
    glyph = x['glyph']
    print(x)
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


STATE_TO_PMOD = {
    'P': dsl.ProteinModification('Ph'),
    'Ub': dsl.ProteinModification('Ub'),
}

SKIP_STATES = {
    'activated',
}


def _states_to_bel(states):
    if not states:
        return
    for state in states:
        if state in STATE_TO_PMOD:
            return STATE_TO_PMOD[state]
        if state in SKIP_STATES:
            return
        logger.debug('unhandled state: %s', state)
        print('$STATE', state)


def _glyph_to_bel(glyph):
    """Convert an entity to BEL."""
    cls = glyph['class']
    entity = glyph.get('entity')
    components = glyph.get('components')

    # print(glyph.keys())
    states = _states_to_bel(glyph.get('states'))

    # compartment = glyph.get('compartment')

    if cls == 'macromolecule' and entity and entity['prefix'] and entity['identifier']:
        rv = dsl.Protein(
            namespace=entity['prefix'],
            identifier=entity['identifier'],
            name=entity['name'],
            variants=states or None,
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
