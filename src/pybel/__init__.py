# -*- coding: utf-8 -*-

"""Parsing, validation, compilation, and data exchange of Biological Expression Language (BEL)."""

from .canonicalize import edge_to_bel, to_bel_script, to_bel_script_gz, to_bel_script_lines
from .dsl import BaseAbundance, BaseEntity
from .io.api import dump, load
from .io.aws import from_s3, to_s3
from .io.bel_commons_client import from_bel_commons, to_bel_commons
from .io.biodati_client import from_biodati, to_biodati
from .io.cx import from_cx, from_cx_file, from_cx_gz, from_cx_jsons, to_cx, to_cx_file, to_cx_gz, to_cx_jsons
from .io.emmaa import from_emmaa
from .io.extras import to_csv, to_gsea, to_sif
from .io.fraunhofer_orientdb import from_fraunhofer_orientdb
from .io.gpickle import (
    from_bytes, from_bytes_gz, from_pickle, from_pickle_gz, to_bytes, to_bytes_gz, to_pickle,
    to_pickle_gz,
)
from .io.graphdati import (
    from_graphdati, from_graphdati_file, from_graphdati_gz, from_graphdati_jsons, to_graphdati, to_graphdati_file,
    to_graphdati_gz, to_graphdati_jsonl, to_graphdati_jsonl_gz, to_graphdati_jsons,
)
from .io.graphml import to_graphml
from .io.hetionet import from_hetionet_file, from_hetionet_gz, from_hetionet_json, get_hetionet
from .io.hipathia import from_hipathia_dfs, from_hipathia_paths, to_hipathia, to_hipathia_dfs
from .io.indra import (
    from_biopax, from_indra_pickle, from_indra_statements, from_indra_statements_json, from_indra_statements_json_file,
    to_indra_statements, to_indra_statements_json, to_indra_statements_json_file,
)
from .io.jgif import (
    from_cbn_jgif, from_cbn_jgif_file, from_jgif, from_jgif_file, from_jgif_gz, from_jgif_jsons, post_jgif, to_jgif,
    to_jgif_file, to_jgif_gz, to_jgif_jsons,
)
from .io.jupyter import to_jupyter, to_jupyter_str
from .io.lines import from_bel_script, from_bel_script_url
from .io.neo4j import to_neo4j
from .io.nodelink import (
    from_nodelink, from_nodelink_file, from_nodelink_gz, from_nodelink_jsons, to_nodelink,
    to_nodelink_file, to_nodelink_gz, to_nodelink_jsons,
)
from .io.pynpa import to_npa_dfs, to_npa_directory
from .io.sbel import from_sbel, from_sbel_file, from_sbel_gz, to_sbel, to_sbel_file, to_sbel_gz
from .io.spia import to_spia_dfs, to_spia_excel, to_spia_tsvs
from .io.triples import to_edgelist, to_triples, to_triples_file
from .io.umbrella_nodelink import to_umbrella_nodelink, to_umbrella_nodelink_file, to_umbrella_nodelink_gz
from .manager import Manager, from_database, to_database
from .parser.parse_bel import parse
from .struct import BELGraph, Pipeline, Query
from .struct.operations import union
from .version import get_version
