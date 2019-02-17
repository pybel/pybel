# -*- coding: utf-8 -*-

"""An example describing a translocation.

.. code-block:: none

    SET Citation = {"PubMed", "16170185"}
    SET Evidence = "These modifications render Ras functional and capable of localizing to the lipid-rich inner surface of the cell membrane. The first and most critical modification, farnesylation, which is principally catalyzed by protein FTase, adds a 15-carbon hydrobobic farnesyl isoprenyl tail to the carboxyl terminus of Ras."
    SET TextLocation = Review

    cat(complex(p(HGNC:FNTA),p(HGNC:FNTB))) directlyIncreases p(SFAM:"RAS Family",pmod(F))
    p(SFAM:"RAS Family",pmod(F)) directlyIncreases tloc(p(SFAM:"RAS Family"),MESHCS:"Intracellular Space",MESHCS:"Cell Membrane")
"""

from ..dsl import activity, complex_abundance, pmod, protein, translocation
from ..language import Entity
from ..struct.graph import BELGraph

__all__ = ['ras_tloc_graph']

ras_tloc_graph = BELGraph(
    name='RAS Transocation Graph',
    version='1.0.0',
    description='The farnesylation of RAS causes its translocation to the cell membrange.'
)

ras_tloc_graph.namespace_url.update({
    'HGNC': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/hgnc-human-genes/hgnc-human-genes-20170725.belns',
    'FPLX': 'https://raw.githubusercontent.com/sorgerlab/famplex/1b7e14ec0fd02ee7ed71514c6e267f57d5641a4b/export/famplex.belns',
    'GO': "https://raw.githubusercontent.com/pharmacome/terminology/1b20f0637c395f8aa89c2e2e342d7b704062c242/external/go-names.belns"
})

evidence = "These modifications render Ras functional and capable of localizing to the lipid-rich inner surface of the cell membrane. The first and most critical modification, farnesylation, which is principally catalyzed by protein FTase, adds a 15-carbon hydrobobic farnesyl isoprenyl tail to the carboxyl terminus of Ras."
pmid = '16170185'

fnta = protein(namespace='HGNC', name='FNTA', identifier='3782')
fntb = protein(namespace='HGNC', name='FNTA', identifier='3785')
fnt = complex_abundance(namespace='FPLX', name='FNT', identifier='RAS', members=[fnta, fntb])
ras = protein(namespace='FPLX', name='RAS', identifier='RAS')
ras_farn = ras.with_variants(pmod('Farn'))

ras_tloc_graph.add_directly_increases(
    fnt,
    ras_farn,
    evidence=evidence,
    citation=pmid,
    subject_modifier=activity('cat'),
)

ras_tloc_graph.add_directly_increases(
    ras_farn,
    ras,
    evidence=evidence,
    citation=pmid,
    object_modifier=translocation(
        from_loc=Entity(namespace='GO', name='intracellular', identifier='GO:0005622'),
        to_loc=Entity(namespace='GO', name='plasma membrane', identifier='GO:0005886'),
    )
)
