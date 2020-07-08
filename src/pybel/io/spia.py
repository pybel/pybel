# -*- coding: utf-8 -*-

"""An exporter for signaling pathway impact analysis (SPIA) described by [Tarca2009]_.

.. [Tarca2009] Tarca, A. L., *et al* (2009). `A novel signaling pathway impact analysis
               <https://doi.org/10.1093/bioinformatics/btn577>`_. Bioinformatics, 25(1), 75–82.

.. seealso:: https://bioconductor.org/packages/release/bioc/html/SPIA.html
"""

import itertools as itt
import os
from collections import OrderedDict
from typing import Dict, Mapping, Set

import pandas as pd

from ..constants import ASSOCIATION, CAUSAL_DECREASE_RELATIONS, CAUSAL_INCREASE_RELATIONS, RELATION
from ..dsl import CentralDogma, Gene, ListAbundance, ProteinModification, Rna
from ..language import pmod_mappings
from ..struct import BELGraph
from ..typing import EdgeData

__all__ = [
    'to_spia_dfs',
    'to_spia_excel',
    'to_spia_tsvs',
]

SPIADataFrames = Mapping[str, pd.DataFrame]

KEGG_RELATIONS = [
    "activation",
    "compound",
    "binding/association",
    "expression",
    "inhibition",
    "activation_phosphorylation",
    "phosphorylation",
    "inhibition_phosphorylation",
    "inhibition_dephosphorylation",
    "dissociation",
    "dephosphorylation",
    "activation_dephosphorylation",
    "state change",
    "activation_indirect effect",
    "inhibition_ubiquination",
    "ubiquination",
    "expression_indirect effect",
    "inhibition_indirect effect",
    "repression",
    "dissociation_phosphorylation",
    "indirect effect_phosphorylation",
    "activation_binding/association",
    "indirect effect",
    "activation_compound",
    "activation_ubiquination"
]


def to_spia_excel(graph: BELGraph, path: str) -> None:
    """Write the BEL graph as an SPIA-formatted excel sheet at the given path."""
    x = to_spia_dfs(graph)
    spia_matrices_to_excel(x, path)


def to_spia_tsvs(graph: BELGraph, directory: str) -> None:
    """Write the BEL graph as a set of SPIA-formatted TSV files in a given directory."""
    x = to_spia_dfs(graph)
    spia_matrices_to_tsvs(x, directory)


def to_spia_dfs(graph: BELGraph) -> SPIADataFrames:
    """Create an excel sheet ready to be used in SPIA software.

    :param graph: BELGraph
    :return: dictionary with matrices
    """
    index_nodes = get_matrix_index(graph)
    spia_matrices = build_spia_matrices(index_nodes)

    for u, v, edge_data in graph.edges(data=True):
        # Both nodes are CentralDogma abundances
        if isinstance(u, CentralDogma) and isinstance(v, CentralDogma):
            # Update matrix dict
            update_spia_matrices(spia_matrices, u, v, edge_data)

        # Subject is CentralDogmaAbundance and node is ListAbundance
        elif isinstance(u, CentralDogma) and isinstance(v, ListAbundance):
            # Add a relationship from subject to each of the members in the object
            for node in v.members:
                # Skip if the member is not in CentralDogma
                if not isinstance(node, CentralDogma):
                    continue

                update_spia_matrices(spia_matrices, u, node, edge_data)

        # Subject is ListAbundance and node is CentralDogmaAbundance
        elif isinstance(u, ListAbundance) and isinstance(v, CentralDogma):
            # Add a relationship from each of the members of the subject to the object
            for node in u.members:
                # Skip if the member is not in CentralDogma
                if not isinstance(node, CentralDogma):
                    continue

                update_spia_matrices(spia_matrices, node, v, edge_data)

        # Both nodes are ListAbundance
        elif isinstance(u, ListAbundance) and isinstance(v, ListAbundance):
            for sub_member, obj_member in itt.product(u.members, v.members):
                # Update matrix if both are CentralDogma
                if isinstance(sub_member, CentralDogma) and isinstance(obj_member, CentralDogma):
                    update_spia_matrices(spia_matrices, sub_member, obj_member, edge_data)

        # else Not valid edge

    return spia_matrices


def get_matrix_index(graph: BELGraph) -> Set[str]:
    """Return set of HGNC names from Proteins/Rnas/Genes/miRNA, nodes that can be used by SPIA."""
    # TODO: Using HGNC Symbols for now
    return {
        node.name
        for node in graph
        if isinstance(node, CentralDogma) and node.namespace.upper() == 'HGNC'
    }


def build_spia_matrices(nodes: Set[str]) -> Dict[str, pd.DataFrame]:
    """Build an adjacency matrix for each KEGG relationship and return in a dictionary.

    :param nodes: A set of HGNC gene symbols
    :return: Dictionary of adjacency matrix for each relationship
    """
    nodes = list(sorted(nodes))

    # Create sheets of the excel in the given order
    matrices = OrderedDict()
    for relation in KEGG_RELATIONS:
        matrices[relation] = pd.DataFrame(0, index=nodes, columns=nodes)

    return matrices


UB_NAMES = {"Ub"} | {e.name for e in pmod_mappings['Ub']['xrefs']}
PH_NAMES = {"Ph"} | {e.name for e in pmod_mappings['Ph']['xrefs']}


def update_spia_matrices(
    spia_matrices: Dict[str, pd.DataFrame],
    u: CentralDogma,
    v: CentralDogma,
    edge_data: EdgeData,
) -> None:
    """Populate the adjacency matrix."""
    if u.namespace.lower() != 'hgnc' or v.namespace.lower() != 'hgnc':
        return

    u_name = u.name
    v_name = v.name
    relation = edge_data[RELATION]

    if relation in CAUSAL_INCREASE_RELATIONS:
        # If it has pmod check which one and add it to the corresponding matrix
        if v.variants and any(isinstance(variant, ProteinModification) for variant in v.variants):
            for variant in v.variants:
                if not isinstance(variant, ProteinModification):
                    continue
                elif variant.entity.name in UB_NAMES:
                    spia_matrices["activation_ubiquination"][u_name][v_name] = 1
                elif variant.entity.name in PH_NAMES:
                    spia_matrices["activation_phosphorylation"][u_name][v_name] = 1
        elif isinstance(v, (Gene, Rna)):  # Normal increase, add activation
            spia_matrices['expression'][u_name][v_name] = 1
        else:
            spia_matrices['activation'][u_name][v_name] = 1

    elif relation in CAUSAL_DECREASE_RELATIONS:
        # If it has pmod check which one and add it to the corresponding matrix
        if v.variants and any(isinstance(variant, ProteinModification) for variant in v.variants):
            for variant in v.variants:
                if not isinstance(variant, ProteinModification):
                    continue
                elif variant.entity.name in UB_NAMES:
                    spia_matrices['inhibition_ubiquination'][u_name][v_name] = 1
                elif variant.entity.name in PH_NAMES:
                    spia_matrices["inhibition_phosphorylation"][u_name][v_name] = 1
        elif isinstance(v, (Gene, Rna)):  # Normal decrease, check which matrix
            spia_matrices["repression"][u_name][v_name] = 1
        else:
            spia_matrices["inhibition"][u_name][v_name] = 1

    elif relation == ASSOCIATION:
        spia_matrices["binding_association"][u_name][v_name] = 1


def spia_matrices_to_excel(spia_matrices: SPIADataFrames, path: str) -> None:
    """Export a SPIA data dictionary into an Excel sheet at the given path.

    .. note::

        # The R import should add the values:
        # ["nodes"] from the columns
        # ["title"] from the name of the file
        # ["NumberOfReactions"] set to "0"
    """
    writer = pd.ExcelWriter(path, engine='xlsxwriter')

    for relation, df in spia_matrices.items():
        df.to_excel(writer, sheet_name=relation, index=False)

    # Save excel
    writer.save()


def spia_matrices_to_tsvs(spia_matrices: SPIADataFrames, directory: str) -> None:
    """Export a SPIA data dictionary into a directory as several TSV documents."""
    os.makedirs(directory, exist_ok=True)
    for relation, df in spia_matrices.items():
        df.to_csv(os.path.join(directory, '{relation}.tsv'.format(relation=relation)), index=True)
