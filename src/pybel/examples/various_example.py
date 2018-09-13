# -*- coding: utf-8 -*-

"""Small graphs with grouped nodes"."""

from ..dsl import abundance, composite_abundance, reaction, protein, complex_abundance
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
    contact='charles.hoyt@scai.fraunhofer.de',
)

single_reaction_graph.namespace_url.update({
    'HGNC': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/hgnc-human-genes/'
            'hgnc-human-genes-20170725.belns',
    'CHEBI': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/chebi/chebi-20170725.belns',
    'GOBP': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/go-biological-process/'
            'go-biological-process-20170725.belns'
})

hk1 = protein(name='HK1', namespace='HGNC', identifier='4922')
atp = abundance(name='ATP', namespace='CHEBI', identifier='15422')
adp = abundance(name='ADP', namespace='CHEBI', identifier='16761')
phosphate = abundance(name='phosphoric acid', namespace='CHEBI', identifier='26078')
glucose = abundance(name='glucose', namespace='CHEBI', identifier='17234')
glucose_6_phosphate = abundance(name='D-glucopyranose 6-phosphate', namespace='CHEBI', identifier='4170')
glycolisis_step_1 = reaction(reactants=[glucose, hk1, atp, phosphate], products=[glucose_6_phosphate, adp, hk1])

composite_example = composite_abundance(members=[glucose_6_phosphate, adp, hk1])
complex_example = complex_abundance(members=[glucose_6_phosphate, adp, hk1])

single_reaction_graph.add_node_from_data(glycolisis_step_1)

single_complex_graph = BELGraph(
    name='Single Complex graph',
    version='1.0.0',
    description="Example graph",
    authors='Charles Tapley Hoyt',
    contact='charles.hoyt@scai.fraunhofer.de',
)

single_complex_graph.namespace_url.update({
    'HGNC': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/hgnc-human-genes/'
            'hgnc-human-genes-20170725.belns',
    'CHEBI': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/chebi/chebi-20170725.belns',
    'GOBP': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/go-biological-process/'
            'go-biological-process-20170725.belns'
})

single_complex_graph.add_node_from_data(complex_example)

single_composite_graph = BELGraph(
    name='Single Composite graph',
    version='1.0.0',
    description="Example graph",
    authors='Charles Tapley Hoyt',
    contact='charles.hoyt@scai.fraunhofer.de',
)

single_composite_graph.namespace_url.update({
    'HGNC': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/hgnc-human-genes/'
            'hgnc-human-genes-20170725.belns',
    'CHEBI': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/chebi/chebi-20170725.belns',
    'GOBP': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/go-biological-process/'
            'go-biological-process-20170725.belns'
})

single_composite_graph.add_node_from_data(composite_example)
