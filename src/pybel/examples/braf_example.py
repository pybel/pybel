# -*- coding: utf-8 -*-

"""An example describing a single evidence about BRAF.

.. code-block::

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

from ..dsl import activity, protein
from ..struct.graph import BELGraph

__all__ = [
    'braf_graph'
]

braf_graph = BELGraph(
    name='BRAF Subgraph',
    version='1.0.0',
    description="Some relations surrounding BRAF",
    authors='Charles Tapley Hoyt',
    contact='charles.hoyt@scai.fraunhofer.de',
)

braf_graph.namespace_url.update({
    'HGNC': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/hgnc-human-genes/hgnc-human-genes-20170725.belns',
})

braf_graph.annotation_url.update({
    'Species': 'https://arty.scai.fraunhofer.de/artifactory/bel/annotation/species-taxonomy-id/species-taxonomy-id-20170511.belanno'
})

thpo = protein(namespace='HGNC', name='THPO', identifier='11795')
braf = protein(namespace='HGNC', name='BRAF', identifier='1097')
raf1 = protein(namespace='HGNC', name='RAF1', identifier='9829')
elk1 = protein(namespace='HGNC', name='ELK1', identifier='3321')

evidence = "Expression of both dominant negative forms, RasN17 and Rap1N17, in UT7-Mpl cells decreased " \
           "thrombopoietin-mediated Elk1-dependent transcription. This suggests that both Ras and Rap1 contribute to " \
           "thrombopoietin-induced ELK1 transcription."

braf_graph.add_increases(
    thpo,
    braf,
    evidence=evidence,
    citation='11283246',
    object_modifier=activity(name='kin'),
    annotations={'Species': '9606'}
)

braf_graph.add_increases(
    thpo,
    raf1,
    evidence=evidence,
    citation='11283246',
    object_modifier=activity(name='kin'),
    annotations={'Species': '9606'}
)

braf_graph.add_increases(
    braf,
    elk1,
    evidence=evidence,
    citation='11283246',
    subject_modifier=activity(name='kin'),
    object_modifier=activity(name='tscript'),
    annotations={'Species': '9606'}
)
