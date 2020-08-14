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

from ..dsl import Abundance, BiologicalProcess, ComplexAbundance, Entity, Protein, ProteinModification, activity
from ..resources import CHEBI_URL, CONFIDENCE_URL, GO_URL, HGNC_URL, SPECIES_PATTERN
from ..struct.graph import BELGraph

__all__ = [
    'sialic_acid_graph',
]

citation = '26438529'

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
    contact='cthoyt@gmail.com',
)

sialic_acid_graph.namespace_url.update({
    'hgnc': HGNC_URL,
    'chebi': CHEBI_URL,
    'go': GO_URL,
})

sialic_acid_graph.annotation_url.update({
    'Confidence': CONFIDENCE_URL,
})

sialic_acid_graph.annotation_pattern.update({
    'Species': SPECIES_PATTERN,
})

sialic_acid = Abundance(name='sialic acid', namespace='chebi', identifier='26667')
cd33 = Protein(
    name='CD33',
    namespace='hgnc',
    identifier='1659',
    xrefs=[
        Entity(namespace='uniprot', identifier='P20138'),
    ],
)
sialic_acid_cd33_complex = ComplexAbundance([sialic_acid, cd33])
shp1 = Protein(namespace='hgnc', name='PTPN6', identifier='9658')
shp2 = Protein(namespace='hgnc', name='PTPN11', identifier='9644')
syk = Protein(namespace='hgnc', name='SYK', identifier='11491')
dap12 = Protein(namespace='hgnc', name='TYROBP', identifier='12449')
trem2 = Protein(namespace='hgnc', name='TREM2', identifier='17761')
cd33_phosphorylated = Protein(name='CD33', namespace='hgnc', identifier='1659', variants=ProteinModification('Ph'))
immune_response = BiologicalProcess(name='immune response', namespace='go', identifier='0006955')

sialic_acid_graph.add_increases(
    sialic_acid_cd33_complex,
    cd33,
    citation=citation,
    annotations={'Species': '9606', 'Confidence': 'High'},
    evidence=evidence_1,
    target_modifier=activity(),
)

sialic_acid_graph.add_increases(
    cd33,
    cd33_phosphorylated,
    citation=citation,
    annotations={'Species': '9606', 'Confidence': 'High'},
    evidence=evidence_1,
    source_modifier=activity(),
)

sialic_acid_graph.add_directly_increases(
    cd33_phosphorylated,
    shp1,
    citation=citation,
    evidence=evidence_1,
    annotations={'Species': '9606', 'Confidence': 'High'},
    source_modifier=activity(),
    target_modifier=activity('phos'),
)

sialic_acid_graph.add_directly_increases(
    cd33_phosphorylated,
    shp2,
    citation=citation,
    evidence=evidence_1,
    annotations={'Species': '9606', 'Confidence': 'High'},
    source_modifier=activity(),
    target_modifier=activity('phos'),
)

sialic_acid_graph.add_directly_decreases(
    shp1,
    syk,
    citation=citation,
    evidence=evidence_2,
    annotations={'Species': '9606', 'Confidence': 'High'},
    source_modifier=activity(),
    target_modifier=activity(),
)

sialic_acid_graph.add_directly_decreases(
    shp2,
    syk,
    citation=citation,
    evidence=evidence_2,
    annotations={'Species': '9606', 'Confidence': 'High'},
    source_modifier=activity(),
    target_modifier=activity(),
)

sialic_acid_graph.add_increases(
    syk,
    trem2,
    citation=citation,
    evidence=evidence_2,
    annotations={'Species': '9606', 'Confidence': 'Low'},
    source_modifier=activity(),
    target_modifier=activity(),
)

sialic_acid_graph.add_increases(
    syk,
    dap12,
    citation=citation,
    evidence=evidence_2,
    annotations={'Species': '9606', 'Confidence': 'Low'},
    source_modifier=activity(),
    target_modifier=activity(),
)
