# -*- coding: utf-8 -*-

"""Export functions for Machine Learning.

While BEL is a fantastic medium for storing metadata and high granularity
information on edges, machine learning algorithms can not consume BEL graphs
directly. This module provides functions that make inferences and interpretations
of BEL graphs in order to interface with machine learning platforms. One
example where we've done this is `BioKEEN <https://doi.org/10.1093/bioinformatics/btz117>`_,
which uses this module to convert BEL graphs into a format for knowledge graph embeddings.
"""

from .api import to_edgelist, to_triples, to_triples_file  # noqa: F401

__all__ = [
    'to_triples_file',
    'to_triples',
    'to_edgelist',
]
