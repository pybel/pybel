# -*- coding: utf-8 -*-

"""Parsing, validation, compilation, and data exchange of Biological Expression Language (BEL)."""

from .canonicalize import edge_to_bel, to_bel_script, to_bel_script_gz, to_bel_script_lines
from .dsl import BaseAbundance, BaseEntity
from .io import (
    dump, from_bel_commons, from_bel_script, from_bel_script_url, from_biodati, from_biopax, from_bytes, from_cbn_jgif,
    from_cbn_jgif_file, from_cx, from_cx_file, from_cx_gz, from_cx_jsons, from_graphdati, from_graphdati_file,
    from_graphdati_gz, from_graphdati_jsons, from_hetionet_file, from_hetionet_gz, from_hetionet_json,
    from_hipathia_dfs, from_hipathia_paths, from_indra_pickle, from_indra_statements, from_indra_statements_json,
    from_indra_statements_json_file, from_jgif, from_jgif_file, from_jgif_gz, from_jgif_jsons, from_nodelink,
    from_nodelink_file, from_nodelink_gz, from_nodelink_jsons, from_pickle, get_hetionet, load, post_jgif,
    to_bel_commons, to_biodati, to_bytes, to_csv, to_cx, to_cx_file, to_cx_gz, to_cx_jsons, to_edgelist, to_graphdati,
    to_graphdati_file, to_graphdati_gz, to_graphdati_jsonl, to_graphdati_jsonl_gz, to_graphdati_jsons, to_graphml,
    to_gsea, to_hipathia, to_hipathia_dfs, to_indra_statements, to_indra_statements_json, to_indra_statements_json_file,
    to_jgif, to_jgif_file, to_jgif_gz, to_jgif_jsons, to_neo4j, to_nodelink, to_nodelink_file, to_nodelink_gz,
    to_nodelink_jsons, to_npa_dfs, to_npa_directory, to_pickle, to_sif, to_tsv, to_umbrella_nodelink,
    to_umbrella_nodelink_file, to_umbrella_nodelink_gz,
)
from .manager import Manager, from_database, to_database
from .struct import BELGraph, Pipeline, Query
from .struct.operations import union
from .version import get_version
