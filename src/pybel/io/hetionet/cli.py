# -*- coding: utf-8 -*-

"""Make hetionet exports."""

import os
from random import choice

import click
import networkx as nx
import pandas as pd
from tqdm.autonotebook import tqdm

from pybel import (
    from_nodelink_gz, get_hetionet, to_bel_script, to_bel_script_gz, to_graphdati_file, to_graphdati_gz,
    to_graphdati_jsonl_gz, to_nodelink_gz,
)
from pybel.canonicalize import edge_to_bel
from pybel.struct.summary.edge_summary import get_metaedge_to_key


@click.command()
@click.option('--directory', default=os.getcwd(), required=True, show_default=True, type=click.Path(dir_okay=True))
def main(directory: str):
    """Make hetionet exports."""
    path = os.path.join(directory, 'hetionet.bel.nodelink.json.gz')
    if not os.path.exists(path):
        graph = get_hetionet()
        to_nodelink_gz(graph, path)
    else:
        click.echo('loading pickle from {}'.format(path))
        graph = from_nodelink_gz(path)

    output_bel_gz_path = os.path.join(directory, 'hetionet.bel.gz')
    if not os.path.exists(output_bel_gz_path):
        click.echo('outputting whole hetionet as BEL GZ to {}'.format(output_bel_gz_path))
        to_bel_script_gz(graph, output_bel_gz_path, use_identifiers=True)

    output_graphdati_jsonl_gz_path = os.path.join(directory, 'hetionet.bel.graphdati.jsonl.gz')
    if not os.path.exists(output_graphdati_jsonl_gz_path):
        click.echo('outputting whole hetionet as BEL GraphDati JSONL GZ to {}'.format(output_graphdati_jsonl_gz_path))
        to_graphdati_jsonl_gz(graph, output_graphdati_jsonl_gz_path, use_identifiers=True)

    output_graphdati_gz_path = os.path.join(directory, 'hetionet.bel.graphdati.json.gz')
    if not os.path.exists(output_graphdati_gz_path):
        click.echo('outputting whole hetionet as BEL GraphDati JSON GZ to {}'.format(output_graphdati_gz_path))
        to_graphdati_gz(graph, output_graphdati_gz_path, use_identifiers=True)

    summary_tsv_path = os.path.join(directory, 'hetionet_summary.tsv')
    if not os.path.exists(summary_tsv_path):
        click.echo('getting metaedges')
        rows = []
        keep_keys = set()
        for value in get_metaedge_to_key(graph).values():
            u, v, key = choice(list(value))
            keep_keys.add(key)
            d = graph[u][v][key]
            bel = edge_to_bel(u, v, d, use_identifiers=True)
            rows.append((key[:8], bel))

        df = pd.DataFrame(rows, columns=['key', 'bel'])
        df.to_csv(summary_tsv_path, sep='\t', index=False)

        non_sample_edges = [
            (u, v, k, d)
            for u, v, k, d in tqdm(graph.edges(keys=True, data=True), desc='Getting non-sample edges to remove')
            if k not in keep_keys
        ]
        click.echo('Removing non-sample edges')
        graph.remove_edges_from(non_sample_edges)
        graph.remove_nodes_from(list(nx.isolates(graph)))

        sample_bel_path = os.path.join(directory, 'hetionet_sample.bel')
        click.echo('outputting sample hetionet in BEL to {}'.format(sample_bel_path))
        to_bel_script(graph, sample_bel_path, use_identifiers=True)

        sample_graphdati_path = os.path.join(directory, 'hetionet_sample.bel.graphdati.json')
        click.echo('outputting sample hetionet in BEL to {}'.format(sample_bel_path))
        to_graphdati_file(graph, sample_graphdati_path, use_identifiers=True, indent=2)


if __name__ == '__main__':
    main()
