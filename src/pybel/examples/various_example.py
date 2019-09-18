# -*- coding: utf-8 -*-

"""Small graphs with grouped nodes"."""

from ..dsl import Abundance, ComplexAbundance, CompositeAbundance, Protein, Reaction
from ..resources import CHEBI_URL, GO_URL, HGNC_URL
from ..struct.graph import BELGraph

__all__ = [
    'single_reaction_graph',
    'single_composite_graph',
    'single_complex_graph',
]

citation = 'None'

evidence = """None""".replace('\n', ' ').strip()

single_reaction_graph = BELGraph(
    name='Single Reaction graph',
    version='1.0.0',
    description="Example graph",
    authors='Charles Tapley Hoyt',
    contact='cthoyt@gmail.com',
)

single_reaction_graph.namespace_url.update({
    'HGNC': HGNC_URL,
    'CHEBI': CHEBI_URL,
    'GO': GO_URL,
})

hk1 = Protein(name='HK1', namespace='HGNC', identifier='4922')
atp = Abundance(name='ATP', namespace='CHEBI', identifier='15422')
adp = Abundance(name='ADP', namespace='CHEBI', identifier='16761')
phosphate = Abundance(name='phosphoric acid', namespace='CHEBI', identifier='26078')
glucose = Abundance(name='glucose', namespace='CHEBI', identifier='17234')
glucose_6_phosphate = Abundance(name='D-glucopyranose 6-phosphate', namespace='CHEBI', identifier='4170')
glycolisis_step_1 = Reaction(reactants=[glucose, hk1, atp, phosphate], products=[glucose_6_phosphate, adp, hk1])

composite_example = CompositeAbundance(members=[glucose_6_phosphate, adp, hk1])
complex_example = ComplexAbundance(members=[glucose_6_phosphate, adp, hk1])

single_reaction_graph.add_node_from_data(glycolisis_step_1)

single_complex_graph = BELGraph(
    name='Single Complex graph',
    version='1.0.0',
    description="Example graph",
    authors='Charles Tapley Hoyt',
    contact='cthoyt@gmail.com',
)

single_complex_graph.namespace_url.update({
    'HGNC': HGNC_URL,
    'CHEBI': CHEBI_URL,
    'GO': GO_URL,
})

single_complex_graph.add_node_from_data(complex_example)

single_composite_graph = BELGraph(
    name='Single Composite graph',
    version='1.0.0',
    description="Example graph",
    authors='Charles Tapley Hoyt',
    contact='cthoyt@gmail.com',
)

single_composite_graph.namespace_url.update({
    'HGNC': HGNC_URL,
    'CHEBI': CHEBI_URL,
    'GO': GO_URL,
})

single_composite_graph.add_node_from_data(composite_example)
