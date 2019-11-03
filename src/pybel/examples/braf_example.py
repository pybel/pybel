# -*- coding: utf-8 -*-

"""An example describing a single evidence about BRAF.

.. code-block:: none

    SET Citation = {"PubMed", "11283246"}
    SET Evidence = "Expression of both dominant negative forms, RasN17 and Rap1N17, in UT7-Mpl cells decreased
    thrombopoietin-mediated Elk1-dependent transcription. This suggests that both Ras and Rap1 contribute to
    thrombopoietin-induced ELK1 transcription."

    SET Species = 9606

    p(HGNC:THPO) increases kin(p(HGNC:BRAF))
    p(HGNC:THPO) increases kin(p(HGNC:RAF1))
    kin(p(HGNC:BRAF)) increases tscript(p(HGNC:ELK1))

    UNSET ALL
"""

from ..dsl import Entity, Protein, activity
from ..resources import HGNC_URL, SPECIES_PATTERN
from ..struct.graph import BELGraph

__all__ = [
    'braf_graph',
]

braf_graph = BELGraph(
    name='BRAF Subgraph',
    version='1.0.0',
    description="Some relations surrounding BRAF",
    authors='Charles Tapley Hoyt',
    contact='cthoyt@gmail.com',
)

braf_graph.namespace_url.update({
    'HGNC': HGNC_URL,
})

braf_graph.annotation_pattern.update({
    'Species': SPECIES_PATTERN,
})

thpo = Protein(
    namespace='HGNC',
    name='THPO',
    identifier='11795',
    xrefs=[
        Entity(namespace='uniprot', identifier='P40225'),
    ],
)
braf = Protein(namespace='HGNC', name='BRAF', identifier='1097')
raf1 = Protein(namespace='HGNC', name='RAF1', identifier='9829')
elk1 = Protein(namespace='HGNC', name='ELK1', identifier='3321')

evidence = "Expression of both dominant negative forms, RasN17 and Rap1N17, in UT7-Mpl cells decreased " \
           "thrombopoietin-mediated Elk1-dependent transcription. This suggests that both Ras and Rap1 contribute to " \
           "thrombopoietin-induced ELK1 transcription."

braf_graph.add_increases(
    thpo,
    braf,
    evidence=evidence,
    citation='11283246',
    object_modifier=activity(name='kin'),
    annotations={'Species': '9606'},
)

braf_graph.add_increases(
    thpo,
    raf1,
    evidence=evidence,
    citation='11283246',
    object_modifier=activity(name='kin'),
    annotations={'Species': '9606'},
)

braf_graph.add_increases(
    braf,
    elk1,
    evidence=evidence,
    citation='11283246',
    subject_modifier=activity(name='kin'),
    object_modifier=activity(name='tscript'),
    annotations={'Species': '9606'},
)
