"""Predicates for checking a node's type."""

from .utils import node_predicate
from ..typing import NodePredicate
from ....dsl import (
    Abundance,
    BaseEntity,
    BiologicalProcess,
    CentralDogma,
    ComplexAbundance,
    CompositeAbundance,
    Gene,
    ListAbundance,
    MicroRna,
    Pathology,
    Population,
    Protein,
    Reaction,
    Rna,
    Transcribable,
)

__all__ = [
    "is_abundance",
    "is_biological_process",
    "is_central_dogma",
    "is_complex",
    "is_composite",
    "is_gene",
    "is_list",
    "is_mirna",
    "is_pathology",
    "is_population",
    "is_protein",
    "is_reaction",
    "is_rna",
    "is_transcribable",
    "not_abundance",
    "not_biological_process",
    "not_central_dogma",
    "not_complex",
    "not_composite",
    "not_gene",
    "not_list",
    "not_mirna",
    "not_pathology",
    "not_population",
    "not_protein",
    "not_reaction",
    "not_rna",
    "not_transcribable",
]


def _type_checker(
    cls: type[BaseEntity] | tuple[type[BaseEntity], ...],
) -> NodePredicate:
    @node_predicate
    def _is_type(node: BaseEntity) -> bool:
        return isinstance(node, cls)

    return _is_type


def _not_type_checker(
    cls: type[BaseEntity] | tuple[type[BaseEntity], ...],
) -> NodePredicate:
    @node_predicate
    def _not_type(node: BaseEntity) -> bool:
        return not isinstance(node, cls)

    return _not_type


is_abundance = _type_checker(Abundance)
not_abundance = _not_type_checker(Abundance)

is_biological_process = _type_checker(BiologicalProcess)
not_biological_process = _not_type_checker(BiologicalProcess)

is_pathology = _type_checker(Pathology)
not_pathology = _not_type_checker(Pathology)

is_population = _type_checker(Population)
not_population = _not_type_checker(Population)

#: Return true if the node is a gene, RNA, miRNA, or Protein
is_central_dogma = _type_checker(CentralDogma)
not_central_dogma = _not_type_checker(CentralDogma)

is_gene = _type_checker(Gene)
not_gene = _not_type_checker(Gene)

is_transcribable = _type_checker(Transcribable)
not_transcribable = _not_type_checker(Transcribable)

is_rna = _type_checker(Rna)
not_rna = _not_type_checker(Rna)

is_mirna = _type_checker(MicroRna)
not_mirna = _not_type_checker(MicroRna)

is_protein = _type_checker(Protein)
not_protein = _not_type_checker(Protein)

is_list = _type_checker(ListAbundance)
not_list = _not_type_checker(ListAbundance)

is_composite = _type_checker(CompositeAbundance)
not_composite = _not_type_checker(CompositeAbundance)

is_complex = _type_checker(ComplexAbundance)
not_complex = _not_type_checker(ComplexAbundance)

is_reaction = _type_checker(Reaction)
not_reaction = _not_type_checker(Reaction)
