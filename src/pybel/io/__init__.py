# -*- coding: utf-8 -*-

"""Input and output functions for BEL graphs.

PyBEL provides multiple lossless interchange options for BEL. Lossy output formats are also included for convenient
export to other programs. Notably, a *de facto* interchange using Resource Description Framework (RDF) to match the
ability of other existing software is excluded due the immaturity of the BEL to RDF mapping.
"""

from .cx import from_cx, from_cx_file, to_cx, to_cx_file
from .extras import to_csv, to_graphml, to_gsea, to_sif
from .gpickle import from_bytes, from_pickle, to_bytes, to_pickle
from .indra import from_biopax, from_indra_pickle, from_indra_statements, to_indra_statements
from .jgif import from_cbn_jgif, from_jgif, post_jgif, to_jgif, to_jgif_file
from .lines import from_bel_script, from_bel_script_url
from .neo4j import to_neo4j
from .nodelink import from_nodelink, from_nodelink_file, to_nodelink, to_nodelink_file
from .tsv import to_edgelist, to_tsv
from .web import from_web, to_web
