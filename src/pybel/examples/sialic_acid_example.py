# -*- coding: utf-8 -*-

"""Curation of the article "Genetics ignite focus on microglial inflammation in Alzheimer's disease".

.. code-block:: none

    SET Citation = {"PubMed", "26438529"}
    SET Evidence = "Sialic acid binding activates CD33, resulting in phosphorylation of the CD33
    immunoreceptor tyrosine-based inhibitory motif (ITIM) domains and activation of the SHP-1 and
    SHP-2 tyrosine phosphatases [66, 67]."



    complex(p(HGNC:CD33),a(CHEBI:"sialic acid")) -> p(HGNC:CD33, pmod(P))
    act(p(HGNC:CD33, pmod(P))) => act(p(HGNC:PTPN6), ma(phos))
    act(p(HGNC:CD33, pmod(P))) => act(p(HGNC:PTPN11), ma(phos))

    UNSET {Evidence, Species}

    SET Evidence = "These phosphatases act on multiple substrates, including Syk, to inhibit immune
    activation [68, 69].  Hence, CD33 activation leads to increased SHP-1 and SHP-2 activity that antagonizes Syk,
    inhibiting ITAM-signaling proteins, possibly including TREM2/DAP12 (Fig. 1, [70, 71])."

    SET Species = 9606

    act(p(HGNC:PTPN6)) =| act(p(HGNC:SYK))
    act(p(HGNC:PTPN11)) =| act(p(HGNC:SYK))
    act(p(HGNC:SYK)) -> act(p(HGNC:TREM2))
    act(p(HGNC:SYK)) -> act(p(HGNC:TYROBP))

    UNSET ALL
"""

from ..constants import (
    ACTIVITY, BEL_DEFAULT_NAMESPACE, CITATION_REFERENCE, CITATION_TYPE, CITATION_TYPE_PUBMED, EFFECT, MODIFIER, NAME,
    NAMESPACE,
)
from ..dsl.nodes import abundance, bioprocess, complex_abundance, pmod, protein
from ..struct.graph import BELGraph

__all__ = [
    'sialic_acid_graph'
]

citation = {
    CITATION_TYPE: CITATION_TYPE_PUBMED,
    CITATION_REFERENCE: '26438529'
}

evidence_1 = """
Sialic acid binding activates CD33, resulting in phosphorylation of the CD33 immunoreceptor tyrosine-based inhibitory
motif (ITIM) domains and activation of the SHP-1 and SHP-2 tyrosine phosphatases [66, 67].
""".replace('\n', ' ').strip()

evidence_2 = """These phosphatases act on multiple substrates, including Syk, to inhibit immune activation [68, 69]. 
Hence, CD33 activation leads to increased SHP-1 and SHP-2 activity that antagonizes Syk, inhibiting ITAM-signaling 
proteins, possibly including TREM2/DAP12 (Fig. 1, [70, 71]).
""".replace('\n', ' ').strip()

sialic_acid_graph = BELGraph(
    name='Sialic Acid Graph',
    version='1.0.0',
    description="The downstream effects of sialic acid in immune signaling",
    authors='Charles Tapley Hoyt',
    contact='charles.hoyt@scai.fraunhofer.de',
)

sialic_acid_graph.namespace_url.update({
    'HGNC': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/hgnc-human-genes/'
            'hgnc-human-genes-20170725.belns',
    'CHEBI': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/chebi/chebi-20170725.belns',
    'GOBP': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/go-biological-process/'
            'go-biological-process-20170725.belns'
})

sialic_acid_graph.annotation_url.update({
    'Confidence': 'https://arty.scai.fraunhofer.de/artifactory/bel/annotation/confidence/confidence-1.0.0.belanno',
    'Species': 'https://arty.scai.fraunhofer.de/artifactory/bel/annotation/species-taxonomy-id/'
               'species-taxonomy-id-20170511.belanno'
})

sialic_acid = abundance(name='sialic acid', namespace='CHEBI', identifier='26667')
cd33 = protein(name='CD33', namespace='HGNC', identifier='1659')
sialic_acid_cd33_complex = complex_abundance([sialic_acid, cd33])
shp1 = protein(namespace='HGNC', name='PTPN6', identifier='9658')
shp2 = protein(namespace='HGNC', name='PTPN11', identifier='9644')
syk = protein(namespace='HGNC', name='SYK', identifier='11491')
dap12 = protein(namespace='HGNC', name='TYROBP', identifier='12449')
trem2 = protein(namespace='HGNC', name='TREM2', identifier='17761')
cd33_phosphorylated = protein(name='CD33', namespace='HGNC', identifier='1659', variants=[pmod('Ph')])
immune_response = bioprocess(name='immune response', namespace='GOBP', identifier='0006955')

sialic_acid_graph.add_increases(
    sialic_acid_cd33_complex,
    cd33,
    citation=citation,
    annotations={'Species': '9606', 'Confidence': 'High'},
    evidence=evidence_1,
    object_modifier={MODIFIER: ACTIVITY}
)

sialic_acid_graph.add_increases(
    cd33,
    cd33_phosphorylated,
    citation=citation,
    annotations={'Species': '9606', 'Confidence': 'High'},
    evidence=evidence_1,
    subject_modifier={MODIFIER: ACTIVITY}
)

sialic_acid_graph.add_directly_increases(
    cd33_phosphorylated,
    shp1,
    citation=citation,
    evidence=evidence_1,
    annotations={'Species': '9606', 'Confidence': 'High'},
    subject_modifier={MODIFIER: ACTIVITY},
    object_modifier={
        MODIFIER: ACTIVITY,
        EFFECT: {
            NAMESPACE: BEL_DEFAULT_NAMESPACE,
            NAME: 'phos'
        }
    }
)

sialic_acid_graph.add_directly_increases(
    cd33_phosphorylated,
    shp2,
    citation=citation,
    evidence=evidence_1,
    annotations={'Species': '9606', 'Confidence': 'High'},
    subject_modifier={MODIFIER: ACTIVITY},
    object_modifier={
        MODIFIER: ACTIVITY,
        EFFECT: {
            NAMESPACE: BEL_DEFAULT_NAMESPACE,
            NAME: 'phos'
        }
    }
)

sialic_acid_graph.add_directly_decreases(
    shp1,
    syk,
    citation=citation,
    evidence=evidence_2,
    annotations={'Species': '9606', 'Confidence': 'High'},
    subject_modifier={MODIFIER: ACTIVITY},
    object_modifier={MODIFIER: ACTIVITY}
)

sialic_acid_graph.add_directly_decreases(
    shp2,
    syk,
    citation=citation,
    evidence=evidence_2,
    annotations={'Species': '9606', 'Confidence': 'High'},
    subject_modifier={MODIFIER: ACTIVITY},
    object_modifier={MODIFIER: ACTIVITY}
)

sialic_acid_graph.add_increases(
    syk,
    trem2,
    citation=citation,
    evidence=evidence_2,
    annotations={'Species': '9606', 'Confidence': 'Low'},
    subject_modifier={MODIFIER: ACTIVITY},
    object_modifier={MODIFIER: ACTIVITY}
)

sialic_acid_graph.add_increases(
    syk,
    dap12,
    citation=citation,
    evidence=evidence_2,
    annotations={'Species': '9606', 'Confidence': 'Low'},
    subject_modifier={MODIFIER: ACTIVITY},
    object_modifier={MODIFIER: ACTIVITY}
)
