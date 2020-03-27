# -*- coding: utf-8 -*-

"""Convert a BEL graph to Hipathia inputs.

Input
-----
SIF File
~~~~~~~~
- Text file with three columns separated by tabs.
- Each row represents an interaction in the pathway. First column is the source
  node, third column the target node, and the second is the type of relation
  between them.
- Only activation and inhibition interactions are allowed.
- The name of the nodes in this file will be stored as the IDs of the nodes.
- The nodes IDs should have the following structure: N (dash) pathway ID (dash)
  node ID.
- Hipathia distinguish between two types of nodes: simple and complex.

Simple nodes:
- Simple nodes may include many genes, but only one is needed to perform the
  function of the node. This could correspond to a protein family of enzymes
  that all have the same function - only one of them needs to be present for
  the action to take place. Simple nodes are defined within
- Node IDs from simple nodes do not include any space, i.e. N-hsa04370-11.

Complex nodes:
- Complex nodes include different simple nodes and represent protein complexes.
  Each simple node within the complex represents one protein in the complex.
  This node requires the presence of all their simple nodes to perform its
  function.
- Node IDs from complex nodes are the juxtaposition of the included simple node
  IDs, separated by spaces, i.e. N-hsa04370-10 26.

ATT File
~~~~~~~~
Text file with twelve (12) columns separated by tabulars. Each row represents a node (either simple or complex).

The columns included are:

1. ``ID``: Node ID as explained above.
2. ``label``: Name to be shown in the picture of the pathway en HGNC. Generally, the gene name of the first
   included EntrezID gene is used as label. For complex nodes, we juxtapose the gene names of the first genes of
   each simple node included (see genesList column below).
3. ``X``: The X-coordinate of the position of the node in the pathway.
4. ``Y``: The Y-coordinate of the position of the node in the pathway.
5. ``color``: The default color of the node.
6. ``shape``: The shape of the node. "rectangle" should be used for genes and "circle" for metabolites.
7. ``type``: The type of the node, either "gene" for genes or "compound" for metabolites. For complex nodes, the
   type of each of their included simple nodes is juxtaposed separated by commas, i.e. gene,gene.
8. ``label.cex``: Amount by which plotting label should be scaled relative to the default.
9. ``label.color``: Default color of the node.
10. ``width``: Default width of the node.
11. ``height``: Default height of the node.
12. ``genesList``: List of genes included in each node, with EntrezID:
  - Simple nodes: EntrezIDs of the genes included, separated by commas (",") and no spaces, i.e. 56848,8877 for
    node N-hsa04370-11.
  - Complex nodes: GenesList of the simple nodes included, separated by a slash ("/") and no spaces, and in the
    same order as in the node ID. For example, node N-hsa04370-10 26 includes two simple nodes: 10 and 26. Its
    genesList column is 5335,5336,/,9047, meaning that the genes included in node 10 are 5335 and 5336, and the
    gene included in node 26 is 9047.

"""

import itertools as itt
import logging
import os
from itertools import groupby
from typing import Dict, List, Union

import networkx as nx
import pandas as pd

import pybel.dsl
from pybel import BELGraph
from pybel.constants import DIRECTLY_DECREASES, DIRECTLY_INCREASES, RELATION
from pybel.dsl import Abundance, BaseAbundance, ComplexAbundance, Protein, hgnc
from pybel.struct import get_children

__all__ = [
    'to_hipathia',
    'HipathiaConverter',
]

logger = logging.getLogger(__name__)


def from_hipathia_paths(name: str, att_path: str, sif_path: str) -> BELGraph:
    """Get a BEL graph from Hipathia files."""
    att_df = pd.read_csv(att_path, sep='\t')
    sif_df = pd.read_csv(sif_path, sep='\t', header=None, names=['source', 'relation', 'target'])
    return from_hipathia_dfs(name=name, att_df=att_df, sif_df=sif_df)


def group_delimited_list(entries: List[str], sep: str = '/') -> List[List[str]]:
    """Group delimited things in a list."""
    return [
        list(b)
        for a, b in groupby(entries, lambda z: z == sep)
        if not a
    ]


def _p(identifier: str):
    return pybel.dsl.Protein(
        namespace='ncbigene',
        identifier=identifier,
        # name=name,
    )


def _f(identifier: str):
    return pybel.dsl.Protein(
        namespace='hipathia.family',
        identifier=identifier,
        # name=name,
    )


def from_hipathia_dfs(name: str, att_df: pd.DataFrame, sif_df: pd.DataFrame) -> BELGraph:
    """Get a BEL graph from Hipathia dataframes."""

    def _clean_name(s):
        prefix = f'N-{name}-'
        if prefix not in s:
            raise ValueError('wrong name for pathway')
        return tuple(sorted(s[len(f'N-{name}-'):].split(' ')))

    att_df['ID'] = att_df['ID'].map(_clean_name)
    att_df['label'] = att_df['label'].str.split(' ')
    att_df['genesList'] = att_df['genesList'].str.split(',').map(group_delimited_list)

    simple_node_to_dsl = {}
    family_node_to_dsl = {}
    complex_node_to_dsl = {}

    graph = BELGraph(name=name)

    for components, component_label_lists, component_gene_lists in att_df[['ID', 'label', 'genesList']].values:
        if not components:
            print(att_df[['ID', 'label', 'genesList']])
            raise ValueError('missing components in row')

        if len(components) == 1:  # This is a simple node, representing a protein or protein family
            component, label, entrez_ids = components[0], component_label_lists[0], component_gene_lists[0]
            if len(entrez_ids) == 1:  # just a protein
                simple_node_to_dsl[component] = _p(identifier=entrez_ids[0])
            else:  # a protein family
                family_dsl = _f(identifier=label)
                for entrez_id in entrez_ids:
                    child_dsl = _p(entrez_id)
                    graph.add_is_a(child_dsl, family_dsl)
                family_node_to_dsl[component] = family_dsl

        else:  # This is a complex node, representing a protein complex of simple nodes
            component_dsls = []
            components = tuple(sorted(components))
            for component, label, entrez_ids in zip(components, component_label_lists, component_gene_lists):
                if len(entrez_ids) == 1:
                    simple_dsl = _p(identifier=entrez_ids[0])
                    simple_node_to_dsl[component] = simple_dsl
                    component_dsls.append(simple_dsl)
                else:
                    family_dsl = _f(identifier=label)
                    for entrez_id in entrez_ids:
                        child_dsl = _p(identifier=entrez_id)
                        graph.add_is_a(child_dsl, family_dsl)
                    family_node_to_dsl[component] = family_dsl
                    component_dsls.append(family_dsl)

            component_dsl = pybel.dsl.ComplexAbundance(component_dsls)
            graph.add_node_from_data(component_dsl)
            complex_node_to_dsl[components] = component_dsl

    # Remap all of the dictionaries
    x = {}
    x.update(complex_node_to_dsl)
    for k, v in simple_node_to_dsl.items():
        x[(k,)] = v
    for k, v in family_node_to_dsl.items():
        x[(k,)] = v

    sif_df['source'] = sif_df['source'].map(_clean_name).map(x.get)
    sif_df['target'] = sif_df['target'].map(_clean_name).map(x.get)
    for source, relation, target in sif_df.values:
        if relation == 'activation':
            graph.add_increases(source, target, citation='', evidence='')
        elif relation == 'inhibition':
            graph.add_decreases(source, target, citation='', evidence='')
        else:
            raise ValueError(f'unknown relation: {relation}')
    return graph


def to_hipathia(graph: BELGraph, directory: str):
    """Export Hipathia artifacts for the graph."""
    converter = HipathiaConverter(graph)
    converter.output(directory=directory)


class HipathiaConverter:
    """A data structure that helps convert a graph to the Hipathia format."""

    bel_node_to_hipathia_node: Dict[BaseAbundance, BaseAbundance]
    bel_node_to_hipathia_genes: Dict[BaseAbundance, List[BaseAbundance]]

    def __init__(self, graph: BELGraph):
        self.graph = graph
        self.name = (self.graph.name or 'pybel-export').lower().replace(' ', '_').replace('-', '_')

        self.bel_node_to_hipathia_node = {}
        self.bel_node_to_hipathia_genes = {}
        self.node_counter = 0
        self.g = nx.MultiDiGraph()

        for u, v, d in self.graph.edges(data=True):
            relation = d[RELATION]
            if isinstance(u, Protein) and isinstance(v, Protein):
                if relation == DIRECTLY_INCREASES:
                    self._add(u, v, 'activation')
                elif relation == DIRECTLY_DECREASES:
                    self._add(u, v, 'inhibition')
            # if isinstance(u, Protein) and isinstance(v, ComplexAbundance):

    def get_att_df(self) -> pd.DataFrame:
        """Get the ATT file dataframe."""

    def get_sif_df(self) -> pd.DataFrame:
        """Get the SIF file dataframe."""

    def _add(self, _u, _v, _relation):
        _u = self._get_or_create_node(_u)
        if _u is None:
            return
        _v = self._get_or_create_node(_v)
        if _v is None:
            return
        return self.g.add_edge(_u, _v, relation=_relation)

    def _get_or_create_node(self, node: Union[Protein, ComplexAbundance, Abundance]):
        if node in self.bel_node_to_hipathia_node:
            return self.bel_node_to_hipathia_node[node]

        if isinstance(node, (Abundance, Protein)):
            self.node_counter += 1
            hipathia_name = f'N-{self.name}-{self.node_counter}'
            self.bel_node_to_hipathia_node[node] = hipathia_name
            if node.namespace.lower() in {'hgnc', 'entrez', 'ncbigene'}:
                self.bel_node_to_hipathia_genes[hipathia_name] = [node]
            elif node.namespace.lower() in {'fplx'}:
                self.bel_node_to_hipathia_genes[hipathia_name] = get_children(self.graph, node)
            return hipathia_name

        # elif isinstance(node, ComplexAbundance):
        #     # TODO: Implement
        #     pass
        raise TypeError(f'Unhandled node type: {type(node)} - {node}')

    def output(self, directory: str):
        """Output the results to the given directory."""
        if not self.g:
            raise RuntimeError('Graph has no nodes')
        if not os.path.exists(directory):
            raise ValueError(f'directory does not exist: {directory}')
        att_path = os.path.join(directory, f'{self.name}.att.tsv')
        sif_path = os.path.join(directory, f'{self.name}.sif.tsv')
        fig_path = os.path.join(directory, f'{self.name}.png')

        with open(sif_path, 'w') as file:
            for u, v, d in self.g.edges(data=True):
                print(u, d['relation'], v, sep='\t', file=file)

        pos = nx.spring_layout(self.g)
        min_x = min(x for x, y in pos.values())
        min_y = min(y for x, y in pos.values())

        def _get_single_gene_list(node: Union[Protein, Abundance]) -> str:
            if node is None:
                raise ValueError('node is none! fuck!')

            try:
                hipathia_genes = self.bel_node_to_hipathia_genes[node]
            except Exception:
                from pprint import pprint
                pprint(self.bel_node_to_hipathia_node)
                pprint(self.bel_node_to_hipathia_genes)
                print(node)
                raise

            if hipathia_genes is None:
                raise ValueError(f'hipathia genes are none for {node}')

            return ','.join(
                n.identifier
                for n in hipathia_genes
            )

        def _get_genes_list(node) -> str:
            if isinstance(node, (Protein, Abundance)):
                return _get_single_gene_list(node)
            elif isinstance(node, ComplexAbundance):
                return ','.join(itt.chain.from_iterable(
                    (_get_single_gene_list(member), '/')
                    for member in node.members
                    if isinstance(member, (Protein, Abundance))
                ))
            else:
                raise TypeError

        with open(att_path, 'w') as file:
            print('ID', 'label', 'X'', Y', 'color', 'shape', 'type', 'label.cex', 'label.color', 'width', 'height',
                  'genesList', sep='\t', file=file)
            for bel_node, hipathia_node in self.bel_node_to_hipathia_node.items():
                x, y = pos[hipathia_node]
                print(
                    hipathia_node,  # ID
                    bel_node.name,  # label
                    int(100 * (x - min_x)),  # X
                    int(100 * (y - min_y)),  # Y
                    'white',  # color
                    'rectangle',  # shape
                    # FIXME should also be able to give list of types
                    'gene' if isinstance(bel_node, (Protein, ComplexAbundance)) else 'metabolite',
                    0.5,  # label.cex
                    'black',  # label.color
                    46,  # width
                    17,  # height
                    _get_genes_list(bel_node),
                    sep='\t',
                    file=file,
                )

        try:
            import matplotlib.pyplot as plt
        except ImportError:
            logger.info('could not import matplotlib')
        else:
            fig, ax = plt.subplots()
            nx.draw(self.g, pos, ax=ax, with_labels=True)
            plt.tight_layout()
            fig.savefig(fig_path)


def make_hsa047370() -> BELGraph:
    """Make an example BEL graph corresponding to the example data from Marina."""
    graph = BELGraph(name='hsa04370')

    node_1 = hgnc('CDC42')
    node_9 = hgnc('KDR')
    node_11 = hgnc('SPHK2')
    node_17 = hgnc('MAPKAPK3')
    node_18 = hgnc('PPP3CA')
    node_19 = hgnc('AKT3')
    node_20 = hgnc('PIK3R5')
    node_21 = hgnc('NFATC2')
    node_22 = hgnc('PRKCA')
    node_24 = hgnc('MAPK14')
    node_27 = hgnc('SRC')
    node_29 = hgnc('VEGFA')
    node_32 = hgnc('MAPK1')
    node_33 = hgnc('MAP2K1')
    node_34 = hgnc('RAF1')
    node_35 = hgnc('HRAS')

    node_10 = ComplexAbundance([hgnc('PLCG1'), hgnc('SH2D2A')])

    node_28 = hgnc('SHC2')
    node_23 = hgnc('PTK2')
    node_25 = hgnc('PXN')
    node_16 = hgnc('HSPB1')
    node_36 = hgnc('NOS3')
    node_37 = hgnc('CASP9')
    node_38 = hgnc('BAD')
    node_39 = hgnc('RAC1')
    node_14 = hgnc('PTGS2')
    node_15 = hgnc('PLA2G4B')

    def _add_increases(a, b):
        graph.add_directly_increases(a, b, citation='', evidence='')

    def _add_decreases(a, b):
        graph.add_directly_decreases(a, b, citation='', evidence='')

    _add_increases(node_1, node_24)
    _add_increases(node_9, node_28)

    _add_increases(node_9, node_23)
    _add_increases(node_9, node_25)
    _add_increases(node_9, node_20)
    _add_increases(node_9, node_27)
    _add_increases(node_9, node_10)

    _add_increases(node_11, node_35)
    _add_increases(node_17, node_16)
    _add_increases(node_18, node_21)
    _add_increases(node_19, node_36)
    _add_decreases(node_19, node_37)
    _add_decreases(node_19, node_38)
    _add_increases(node_20, node_39)
    _add_increases(node_20, node_19)
    _add_increases(node_21, node_14)
    _add_increases(node_22, node_34)
    _add_increases(node_22, node_11)
    _add_increases(node_24, node_17)
    _add_increases(node_27, node_20)
    _add_increases(node_29, node_9)
    _add_increases(node_32, node_15)
    _add_increases(node_33, node_32)
    _add_increases(node_34, node_33)
    _add_increases(node_35, node_34)
    _add_increases(node_10, node_18)
    _add_increases(node_10, node_22)
    _add_increases(node_10, node_15)
    _add_increases(node_10, node_36)

    return graph


def _main():
    graph = from_hipathia_paths(
        name='hsa04370',
        att_path='/Users/cthoyt/dev/bel/pybel/tests/test_io/test_hipathia/hsa04370.att',
        sif_path='/Users/cthoyt/dev/bel/pybel/tests/test_io/test_hipathia/hsa04370.sif',
    )
    pybel.to_bel_script(graph, '/Users/cthoyt/dev/bel/pybel/tests/test_io/test_hipathia/hsa04370.bel')

    # desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    # to_hipathia(
    #     make_hsa047370(),
    #     directory=desktop,
    # )


if __name__ == '__main__':
    _main()
