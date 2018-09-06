# -*- coding: utf-8 -*-

"""This directory contains example networks, precompiled as BEL graphs that are appropriate to use in examples."""

from .braf_example import braf_graph
from .egf_example import egf_graph
from .homology_example import homology_graph
from .sialic_acid_example import sialic_acid_graph
from .statin_example import statin_graph
from .tloc_example import ras_tloc_graph

__all__ = [
    'egf_graph',
    'sialic_acid_graph',
    'statin_graph',
    'braf_graph',
    'homology_graph',
    'ras_tloc_graph',
]
