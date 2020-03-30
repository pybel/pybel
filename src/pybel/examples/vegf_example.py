# -*- coding: utf-8 -*-

"""An example graph in which a family activates another family."""

from ..dsl import Protein
from ..struct import BELGraph

vegf_graph = BELGraph()
vegf = Protein(namespace='fplx', name='VEGF')
vegfr = Protein(namespace='fplx', name='VEGFR')

ev = 'VEGF activates the endothelial VEGF receptors' \
     ' (VEGFR) 1 and 2, and VEGF-C activates VEGFR-3 and VEGFR-2.'

vegf_graph.add_activates(
    vegf,
    vegfr,
    evidence=ev,
    citation='9506953',
)
