# -*- coding: utf-8 -*-

"""An example graph in which a famplex (complex of families) activates something."""

from ..dsl import ComplexAbundance, NamedComplexAbundance, Protein, ProteinModification
from ..struct import BELGraph

ampk_graph = BELGraph()
ampk = NamedComplexAbundance(namespace='fplx', name='AMPK')

# Alpha subunits of AMPK
ampk_alpha = Protein(namespace='fplx', name='AMPK_alpha')
ampk_graph.add_part_of(ampk_alpha, ampk)

prkaa1 = Protein(namespace='hgnc', identifier='9376', name='PRKAA1')
prkaa2 = Protein(namespace='hgnc', identifier='9377', name='PRKAA2')
ampk_graph.add_is_a(prkaa1, ampk_alpha)
ampk_graph.add_is_a(prkaa2, ampk_alpha)

# Beta subunits of AMPK
ampk_beta = Protein(namespace='fplx', name='AMPK_beta')
ampk_graph.add_part_of(ampk_beta, ampk)

prkab1 = Protein(namespace='hgnc', identifier='9378', name='PRKAB1')
prkab2 = Protein(namespace='hgnc', identifier='9379', name='PRKAB2')
ampk_graph.add_is_a(prkab1, ampk_beta)
ampk_graph.add_is_a(prkab2, ampk_beta)

# Gamma subunits of AMPK
ampk_gamma = Protein(namespace='fplx', name='AMPK_gamma')
ampk_graph.add_part_of(ampk_gamma, ampk)

prkag1 = Protein(namespace='hgnc', identifier='9385', name='PRKAG1')
prkag2 = Protein(namespace='hgnc', identifier='9386', name='PRKAG2')
prkag3 = Protein(namespace='hgnc', identifier='9387', name='PRKAG3')
ampk_graph.add_is_a(prkag1, ampk_gamma)
ampk_graph.add_is_a(prkag2, ampk_gamma)
ampk_graph.add_is_a(prkag3, ampk_gamma)

mtorc1 = NamedComplexAbundance(namespace='fplx', name='mTORC1')
mtor = Protein(namespace='hgnc', identifier='3942', name='MTOR')
rptor = Protein(namespace='hgnc', identifier='30287', name='RPTOR')
ampk_graph.add_part_of(mtor, mtorc1)
ampk_graph.add_part_of(rptor, mtorc1)

# FamPlex says this is a family but I thought it was a complex
p14_3_3 = Protein(namespace='fplx', name='p14_3_3')

ev = "We report here that AMPK directly phosphorylates the" \
     " mTOR binding partner raptor on two well conserved serine" \
     " residues, and this phosphorylation induces 14-3-3" \
     " binding to raptor."

ampk_graph.add_directly_phosphorylates(
    ampk,
    rptor,
    'Ser',  # on Ser722 and Ser792
    evidence=ev,
    citation='18439900',
)
ampk_graph.add_binds(
    ComplexAbundance([
        rptor.with_variants(ProteinModification('Ser')),
        mtor,
    ]),
    p14_3_3,
    evidence=ev,
    citation='18439900',
)
