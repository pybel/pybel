# -*- coding: utf-8 -*-

"""An example describing EGF's effect on cellular processes.

.. code-block:: none

    SET Citation = {"PubMed","Clin Cancer Res 2003 Jul 9(7) 2416-25","12855613"}
    SET Evidence = "This induction was not seen either when LNCaP cells were treated with flutamide or conditioned medium were pretreated with antibody to the epidermal growth factor (EGF)"
    SET Species = 9606

    tscript(p(HGNC:AR)) increases p(HGNC:EGF)

    UNSET ALL

    SET Citation = {"PubMed","Int J Cancer 1998 Jul 3 77(1) 138-45","9639405"}
    SET Evidence = "DU-145 cells treated with 5000 U/ml of IFNgamma and IFN alpha, both reduced EGF production with IFN gamma reduction more significant."
    SET Species = 9606

    p(HGNC:IFNA1) decreases p(HGNC:EGF)
    p(HGNC:IFNG) decreases p(HGNC:EGF)

    UNSET ALL


    SET Citation = {"PubMed","DNA Cell Biol 2000 May 19(5) 253-63","10855792"}
    SET Evidence = "Although found predominantly in the cytoplasm and, less abundantly, in the nucleus, VCP can be translocated from the nucleus after stimulation with epidermal growth factor."
    SET Species = 9606

    p(HGNC:EGF) increases tloc(p(HGNC:VCP), GO:nucleus, GO:cytoplasm)

    UNSET ALL

    SET Citation = {"PubMed","J Clin Oncol 2003 Feb 1 21(3) 447-52","12560433"}
    SET Evidence = "Valosin-containing protein (VCP; also known as p97) has been shown to be associated with antiapoptotic function and metastasis via activation of the nuclear factor-kappaB signaling pathway."
    SET Species = 9606

    cat(p(HGNC:VCP)) increases tscript(complex(p(HGNC:NFKB1), p(HGNC:NFKB2), p(HGNC:REL), p(HGNC:RELA), p(HGNC:RELB)))
    tscript(complex(p(HGNC:NFKB1), p(HGNC:NFKB2), p(HGNC:REL), p(HGNC:RELA), p(HGNC:RELB))) decreases bp(MESHPP:Apoptosis)

    UNSET ALL
"""

from ..dsl import BiologicalProcess, ComplexAbundance, Protein, activity, translocation
from ..language import cytoplasm, nucleus
from ..resources import CHEBI_URL, CONFIDENCE_URL, GO_URL, HGNC_URL, SPECIES_PATTERN
from ..struct.graph import BELGraph

__all__ = [
    'egf_graph',
]

egf_graph = BELGraph(
    name='EGF Pathway',
    version='1.0.0',
    description="The downstream effects of EGF",
    authors='Charles Tapley Hoyt',
    contact='cthoyt@gmail.com',
)

egf_graph.namespace_url.update({
    'hgnc': HGNC_URL,
    'chebi': CHEBI_URL,
    'go': GO_URL,
})

egf_graph.annotation_url.update({
    'Confidence': CONFIDENCE_URL,
})

egf_graph.annotation_pattern.update({
    'Species': SPECIES_PATTERN,
})

ar = Protein(name='AR', namespace='hgnc')
egf = Protein(name='EGF', namespace='hgnc')
ifna1 = Protein(name='IFNA1', namespace='hgnc')
ifng = Protein(name='IFNG', namespace='hgnc')
vcp = Protein(name='VCP', namespace='hgnc')

nfkb1 = Protein(name='NFKB1', namespace='hgnc')
nfkb2 = Protein(name='NFKB2', namespace='hgnc')
rel = Protein(name='REL', namespace='hgnc')
rela = Protein(name='RELA', namespace='hgnc')
relb = Protein(name='RELB', namespace='hgnc')

nfkb_complex = ComplexAbundance([nfkb1, nfkb2, rel, rela, relb])

apoptosis = BiologicalProcess(namespace='go', name='apoptotic process', identifier='0006915')

egf_graph.add_increases(
    ar,
    egf,
    citation='12855613',
    evidence='This induction was not seen either when LNCaP cells were treated with flutamide or conditioned medium '
             'were pretreated with antibody to the epidermal growth factor (EGF)',
    annotations={'Species': '9606'},
    source_modifier=activity('tscript'),
)

egf_graph.add_decreases(
    ifna1,
    egf,
    citation='9639405',
    evidence='DU-145 cells treated with 5000 U/ml of IFNgamma and IFN alpha, both reduced EGF production with IFN '
             'gamma reduction more significant.',
    annotations={'Species': '9606'},
)

egf_graph.add_decreases(
    ifng,
    egf,
    citation='9639405',
    evidence='DU-145 cells treated with 5000 U/ml of IFNgamma and IFN alpha, both reduced EGF production with IFN '
             'gamma reduction more significant.',
    annotations={'Species': '9606'},
)

egf_graph.add_increases(
    egf,
    vcp,
    citation='10855792',
    evidence='Although found predominantly in the cytoplasm and, less abundantly, in the nucleus, VCP can be '
             'translocated from the nucleus after stimulation with epidermal growth factor.',
    annotations={'Species': '9606'},
    target_modifier=translocation(
        from_loc=nucleus,
        to_loc=cytoplasm,
    ),
)

egf_graph.add_increases(
    vcp,
    nfkb_complex,
    citation='12560433',
    evidence="Valosin-containing protein (VCP; also known as p97) has been shown to be associated with antiapoptotic"
             " function and metastasis via activation of the nuclear factor-kappaB signaling pathway.",
    annotations={'Species': '9606'},
    source_modifier=activity('cat'),
    target_modifier=activity('tscript'),
)

egf_graph.add_decreases(
    nfkb_complex,
    apoptosis,
    citation='12560433',
    evidence="Valosin-containing protein (VCP; also known as p97) has been shown to be associated with antiapoptotic "
             "function and metastasis via activation of the nuclear factor-kappaB signaling pathway.",
    annotations={'Species': '9606'},
    source_modifier=activity('tscript'),
)
