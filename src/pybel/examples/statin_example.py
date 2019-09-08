# -*- coding: utf-8 -*-

"""An example describing statins."""

from ..dsl import Abundance, Protein
from ..struct.graph import BELGraph

__all__ = [
    'statin_graph'
]

statin_graph = BELGraph(
    name='Statin Graph',
    version='1.0.1',
    description="The effects of statins from ChEBI",
    authors='Charles Tapley Hoyt',
    contact='charles.hoyt@scai.fraunhofer.de',
)

statin_graph.namespace_url.update({
    'HGNC': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/hgnc-human-genes/hgnc-human-genes-20170725.belns',
    'CHEBI': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/chebi/chebi-20170725.belns',
    'EC': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/enzyme-class/enzyme-class-20170508.belns'
})

statin_graph.annotation_url.update({
    'Confidence': 'https://arty.scai.fraunhofer.de/artifactory/bel/annotation/confidence/confidence-1.0.0.belanno',
})

fluvastatin = Abundance(namespace='CHEBI', name='fluvastatin', identifier='38561')
avorastatin = Abundance(namespace='CHEBI', name='atorvastatin', identifier='39548')
synthetic_statin = Abundance(namespace='CHEBI', name='statin (synthetic)', identifier='87635')
statin = Abundance(namespace='CHEBI', name='statin', identifier='87631')
mevinolinic_acid = Abundance(namespace='CHEBI', name='mevinolinic acid', identifier='82985')
hmgcr_inhibitor = Abundance(namespace='CHEBI', identifier='35664',
                            name='EC 1.1.1.34/EC 1.1.1.88 (hydroxymethylglutaryl-CoA reductase) inhibitor')
ec_11134 = Protein(namespace='EC', name='1.1.1.34')
ec_11188 = Protein(namespace='EC', name='1.1.1.88')

hmgcr = Protein(namespace='HGNC', name='HMGCR', identifier='5006')

statin_graph.add_is_a(avorastatin, synthetic_statin)
statin_graph.add_is_a(fluvastatin, synthetic_statin)
statin_graph.add_is_a(synthetic_statin, statin)
statin_graph.add_is_a(statin, hmgcr_inhibitor)
statin_graph.add_is_a(mevinolinic_acid, hmgcr_inhibitor)

statin_graph.add_is_a(hmgcr, ec_11134)

statin_graph.add_inhibits(
    hmgcr_inhibitor,
    ec_11134,
    evidence='From ChEBI',
    citation='23180789',
    annotations={
        'Confidence': 'Axiomatic',
    },
)

statin_graph.add_inhibits(
    hmgcr_inhibitor,
    ec_11188,
    evidence='From ChEBI',
    citation='23180789',
    annotations={
        'Confidence': 'Axiomatic',
    },
)
