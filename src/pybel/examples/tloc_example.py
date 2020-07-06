# -*- coding: utf-8 -*-

"""An example describing a translocation.

.. code-block:: none

    SET Citation = {"PubMed", "16170185"}
    SET Evidence = "These modifications render Ras functional and capable of localizing to the lipid-rich inner surface of the cell membrane. The first and most critical modification, farnesylation, which is principally catalyzed by protein FTase, adds a 15-carbon hydrobobic farnesyl isoprenyl tail to the carboxyl terminus of Ras."
    SET TextLocation = Review

    cat(complex(p(HGNC:FNTA),p(HGNC:FNTB))) directlyIncreases p(SFAM:"RAS Family",pmod(F))
    p(SFAM:"RAS Family",pmod(F)) directlyIncreases tloc(p(SFAM:"RAS Family"),MESHCS:"Intracellular Space",MESHCS:"Cell Membrane")
"""

from ..dsl import ComplexAbundance, Protein, ProteinModification, activity, translocation
from ..language import Entity
from ..resources import FPLX_URL, GO_URL, HGNC_URL
from ..struct.graph import BELGraph

__all__ = [
    'ras_tloc_graph',
]

ras_tloc_graph = BELGraph(
    name='RAS Transocation Graph',
    version='1.0.1',
    description='The farnesylation of RAS causes its translocation to the cell membrane.',
    authors='Charles Tapley Hoyt',
    contact='cthoyt@gmail.com',
)

ras_tloc_graph.namespace_url.update({
    'HGNC': HGNC_URL,
    'GO': GO_URL,
    'FPLX': FPLX_URL,
})

evidence = "These modifications render Ras functional and capable of localizing to the lipid-rich inner surface of the cell membrane. The first and most critical modification, farnesylation, which is principally catalyzed by protein FTase, adds a 15-carbon hydrobobic farnesyl isoprenyl tail to the carboxyl terminus of Ras."
pmid = '16170185'

fnta = Protein(namespace='HGNC', name='FNTA', identifier='3782')
fntb = Protein(namespace='HGNC', name='FNTA', identifier='3785')
fnt = ComplexAbundance(namespace='FPLX', name='FNT', identifier='RAS', members=[fnta, fntb])
ras = Protein(namespace='FPLX', name='RAS', identifier='RAS')
ras_farn = ras.with_variants(ProteinModification('Farn'))

ras_tloc_graph.add_directly_increases(
    fnt,
    ras_farn,
    evidence=evidence,
    citation=pmid,
    source_modifier=activity('cat'),
)

ras_tloc_graph.add_directly_increases(
    ras_farn,
    ras,
    evidence=evidence,
    citation=pmid,
    target_modifier=translocation(
        from_loc=Entity(namespace='GO', name='intracellular', identifier='GO:0005622'),
        to_loc=Entity(namespace='GO', name='plasma membrane', identifier='GO:0005886'),
    ),
)
