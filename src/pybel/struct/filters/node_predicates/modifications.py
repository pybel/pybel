# -*- coding: utf-8 -*-

"""Predicates for checking nodes' variants."""

from functools import wraps
from typing import Tuple, Type, Union

from .utils import node_predicate
from ..typing import NodePredicate
from ....dsl import BaseEntity, CentralDogma, Fragment, GeneModification, Hgvs, ProteinModification, Variant

__all__ = [
    'has_variant',
    'has_protein_modification',
    'has_gene_modification',
    'has_fragment',
    'has_hgvs',
]


@node_predicate
def has_variant(node: BaseEntity) -> bool:
    """Return true if the node has any variants."""
    return isinstance(node, CentralDogma) and node.variants


def _variant_checker(variant_cls: Union[Type[Variant], Tuple[Type[Variant], ...]]) -> NodePredicate:
    @node_predicate
    @wraps(node_has_variant)
    def _rv(node: BaseEntity):
        return node_has_variant(node, variant_cls)

    return _rv


def node_has_variant(node: BaseEntity, variant_cls) -> bool:
    """Return true if the node has at least one of the given variant."""
    return isinstance(node, CentralDogma) and node.variants and any(
        isinstance(variant, variant_cls)
        for variant in node.variants
    )


has_protein_modification = _variant_checker(ProteinModification)
has_gene_modification = _variant_checker(GeneModification)
has_hgvs = _variant_checker(Hgvs)
has_fragment = _variant_checker(Fragment)
