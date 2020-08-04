# -*- coding: utf-8 -*-

"""Input and output functions for BEL graphs.

PyBEL provides multiple lossless interchange options for BEL. Lossy output formats are also included for convenient
export to other programs. Notably, a *de facto* interchange using Resource Description Framework (RDF) to match the
ability of other existing software is excluded due the immaturity of the BEL to RDF mapping.
"""

from .api import dump, load
from .aws import from_s3, to_s3
from .bel_commons_client import from_bel_commons, to_bel_commons
from .biodati_client import from_biodati, to_biodati
from .cx import from_cx, from_cx_file, from_cx_gz, from_cx_jsons, to_cx, to_cx_file, to_cx_gz, to_cx_jsons
from .emmaa import from_emmaa
from .extras import to_csv, to_gsea, to_sif
from .fraunhofer_orientdb import from_fraunhofer_orientdb
from .gpickle import (
    from_bytes, from_bytes_gz, from_pickle, from_pickle_gz, to_bytes, to_bytes_gz, to_pickle,
    to_pickle_gz,
)
from .graphdati import (
    from_graphdati, from_graphdati_file, from_graphdati_gz, from_graphdati_jsons, to_graphdati, to_graphdati_file,
    to_graphdati_gz, to_graphdati_jsonl, to_graphdati_jsonl_gz, to_graphdati_jsons,
)
from .graphml import to_graphml
from .hetionet import from_hetionet_file, from_hetionet_gz, from_hetionet_json, get_hetionet
from .hipathia import from_hipathia_dfs, from_hipathia_paths, to_hipathia, to_hipathia_dfs
from .indra import (
    from_biopax, from_indra_pickle, from_indra_statements, from_indra_statements_json, from_indra_statements_json_file,
    to_indra_statements, to_indra_statements_json, to_indra_statements_json_file,
)
from .jgif import (
    from_cbn_jgif, from_cbn_jgif_file, from_jgif, from_jgif_file, from_jgif_gz, from_jgif_jsons, post_jgif, to_jgif,
    to_jgif_file, to_jgif_gz, to_jgif_jsons,
)
from .jupyter import to_jupyter, to_jupyter_str
from .lines import from_bel_script, from_bel_script_url
from .neo4j import to_neo4j
from .nodelink import (
    from_nodelink, from_nodelink_file, from_nodelink_gz, from_nodelink_jsons, to_nodelink,
    to_nodelink_file, to_nodelink_gz, to_nodelink_jsons,
)
from .pynpa import to_npa_dfs, to_npa_directory
from .sbel import from_sbel, from_sbel_file, from_sbel_gz, to_sbel, to_sbel_file, to_sbel_gz
from .spia import to_spia_dfs, to_spia_excel, to_spia_tsvs
from .triples import to_edgelist, to_triples, to_triples_file
from .umbrella_nodelink import to_umbrella_nodelink, to_umbrella_nodelink_file, to_umbrella_nodelink_gz
