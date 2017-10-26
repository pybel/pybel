# -*- coding: utf-8 -*-

"""This is the first attempt at curating an excerpt from the research article, "Genetics ignite focus on microglial
inflammation in Alzheimer's disease".

.. code-block:: none

    SET Citation = {"PubMed", "26438529"}
    SET Evidence = "Sialic acid binding activates CD33, resulting in phosphorylation of the CD33 immunoreceptor tyrosine-based inhibitory motif (ITIM) domains and activation of the SHP-1 and SHP-2 tyrosine phosphatases [66, 67]."
    SET Species = 9606

    complex(p(HGNC:CD33),a(CHEBI:"sialic acid")) -> p(HGNC:CD33, pmod(P))
    act(p(HGNC:CD33, pmod(P))) => act(p(HGNC:PTPN6), ma(phos))
    act(p(HGNC:CD33, pmod(P))) => act(p(HGNC:PTPN11), ma(phos))

    UNSET {Evidence, Species}
    SET Evidence = "These phosphatases act on multiple substrates, including Syk, to inhibit immune activation [68, 69].  Hence, CD33 activation leads to increased SHP-1 and SHP-2 activity that antagonizes Syk, inhibiting ITAM-signaling proteins, possibly including TREM2/DAP12 (Fig. 1, [70, 71])."

    act(p(HGNC:PTPN6)) =| act(p(HGNC:SYK))
    act(p(HGNC:PTPN11)) =| act(p(HGNC:SYK))
    act(p(HGNC:SYK)) -> act(p(HGNC:TREM2))
    act(p(HGNC:SYK)) -> act(p(HGNC:TYROBP))

    UNSET ALL
"""

from ..constants import *
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
    'HGNC': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/hgnc-human-genes/hgnc-human-genes-20170725.belns',
    'CHEBI': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/chebi/chebi-20170725.belns',
    'GOBP': 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/go-biological-process/go-biological-process-20170725.belns'
})

sialic_acid_graph.annotation_url.update({
    'Confidence': 'https://arty.scai.fraunhofer.de/artifactory/bel/annotation/confidence/confidence-1.0.0.belanno',
    'Species': 'https://arty.scai.fraunhofer.de/artifactory/bel/annotation/species-taxonomy-id/species-taxonomy-id-20170511.belanno'
})

sialic_acid = {
    FUNCTION: ABUNDANCE,
    NAMESPACE: 'CHEBI',
    NAME: 'sialic acid',
    ID: '26667'
}

cd33 = {
    FUNCTION: PROTEIN,
    NAMESPACE: 'HGNC',
    NAME: 'CD33',
    ID: '1659'
}

sialic_acid_cd33_complex = {
    FUNCTION: COMPLEX,
    MEMBERS: [
        sialic_acid,
        cd33
    ]
}

cd33_phosphorylated = {
    FUNCTION: PROTEIN,
    NAMESPACE: 'HGNC',
    NAME: 'CD33',
    VARIANTS: [
        {
            KIND: PMOD,
            IDENTIFIER: {
                NAMESPACE: BEL_DEFAULT_NAMESPACE,
                NAME: 'Ph'
            }
        }
    ],
    ID: '1659'
}

shp1 = {
    FUNCTION: PROTEIN,
    NAMESPACE: 'HGNC',
    NAME: 'PTPN6',
    ID: '9658'
}

shp2 = {
    FUNCTION: PROTEIN,
    NAMESPACE: 'HGNC',
    NAME: 'PTPN11',
    ID: '9644'
}

syk = {
    FUNCTION: PROTEIN,
    NAMESPACE: 'HGNC',
    NAME: 'SYK',
    ID: '11491'
}

dap12 = {
    FUNCTION: PROTEIN,
    NAMESPACE: 'HGNC',
    NAME: 'TYROBP',
    ID: '12449'
}

trem2 = {
    FUNCTION: PROTEIN,
    NAMESPACE: 'HGNC',
    NAME: 'TREM2',
    ID: '17761'
}

immune_response = {
    FUNCTION: BIOPROCESS,
    NAMESPACE: 'GOBP',
    NAME: 'immune response',
    ID: '0006955'
}

sialic_acid_graph.add_qualified_edge(
    sialic_acid_cd33_complex,
    cd33,
    relation=INCREASES,
    citation=citation,
    annotations={'Species': '9606', 'Confidence': 'High'},
    evidence=evidence_1,
    object_modifier={MODIFIER: ACTIVITY}
)

sialic_acid_graph.add_qualified_edge(
    cd33,
    cd33_phosphorylated,
    relation=INCREASES,
    citation=citation,
    annotations={'Species': '9606', 'Confidence': 'High'},
    evidence=evidence_1,
    subject_modifier={MODIFIER: ACTIVITY}
)

sialic_acid_graph.add_qualified_edge(
    cd33_phosphorylated,
    shp1,
    relation=DIRECTLY_INCREASES,
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

sialic_acid_graph.add_qualified_edge(
    cd33_phosphorylated,
    shp2,
    relation=DIRECTLY_INCREASES,
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

sialic_acid_graph.add_qualified_edge(
    shp1,
    syk,
    relation=DIRECTLY_DECREASES,
    citation=citation,
    evidence=evidence_2,
    annotations={'Species': '9606', 'Confidence': 'High'},
    subject_modifier={MODIFIER: ACTIVITY},
    object_modifier={MODIFIER: ACTIVITY}
)

sialic_acid_graph.add_qualified_edge(
    shp2,
    syk,
    relation=DIRECTLY_DECREASES,
    citation=citation,
    evidence=evidence_2,
    annotations={'Species': '9606', 'Confidence': 'High'},
    subject_modifier={MODIFIER: ACTIVITY},
    object_modifier={MODIFIER: ACTIVITY}
)

sialic_acid_graph.add_qualified_edge(
    syk,
    trem2,
    relation=INCREASES,
    citation=citation,
    evidence=evidence_2,
    annotations={'Species': '9606', 'Confidence': 'Low'},
    subject_modifier={MODIFIER: ACTIVITY},
    object_modifier={MODIFIER: ACTIVITY}
)

sialic_acid_graph.add_qualified_edge(
    syk,
    dap12,
    relation=INCREASES,
    citation=citation,
    evidence=evidence_2,
    annotations={'Species': '9606', 'Confidence': 'Low'},
    subject_modifier={MODIFIER: ACTIVITY},
    object_modifier={MODIFIER: ACTIVITY}
)
