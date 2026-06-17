"""TSV conversion."""

import json
import logging
from typing import TextIO

from networkx.utils import open_file
from tqdm.autonotebook import tqdm

from . import converters
from ...dsl import BaseEntity
from ...struct import BELGraph

__all__ = [
    "to_edgelist",
    "to_triple",
    "to_triples",
    "to_triples_file",
]

logger = logging.getLogger(__name__)


class NoTriplesValueError(ValueError):
    """Raised when no triples could be converted."""


@open_file(1, mode="w")
def to_triples_file(
    graph: BELGraph,
    path: str | TextIO,
    *,
    use_tqdm: bool = False,
    sep="\t",
    raise_on_none: bool = False,
) -> None:
    """Write the graph as a TSV.

    :param graph: A BEL graph
    :param path: A path or file-like
    :param use_tqdm: Should a progress bar be shown?
    :param sep: The separator to use
    :param raise_on_none: Should an exception be raised if no triples are returned?
    :raises: NoTriplesValueError
    """
    for h, r, t in to_triples(graph, use_tqdm=use_tqdm, raise_on_none=raise_on_none):
        print(h, r, t, sep=sep, file=path)


@open_file(1, mode="w")
def to_edgelist(
    graph: BELGraph,
    path: str | TextIO,
    *,
    use_tqdm: bool = False,
    sep="\t",
    raise_on_none: bool = False,
) -> None:
    """Write the graph as an edgelist.

    :param graph: A BEL graph
    :param path: A path or file-like
    :param use_tqdm: Should a progress bar be shown?
    :param sep: The separator to use
    :param raise_on_none: Should an exception be raised if no triples are returned?
    :raises: NoTriplesValueError
    """
    for h, r, t in to_triples(graph, use_tqdm=use_tqdm, raise_on_none=raise_on_none):
        print(h, t, json.dumps({"relation": r}), sep=sep, file=path)


def to_triples(graph: BELGraph, use_tqdm: bool = False, raise_on_none: bool = False) -> list[tuple[str, str, str]]:
    """Get a non-redundant list of triples representing the graph.

    :param graph: A BEL graph
    :param use_tqdm: Should a progress bar be shown?
    :param raise_on_none: Should an exception be raised if no triples are returned?
    :raises: NoTriplesValueError
    """
    it = graph.edges(keys=True)

    if use_tqdm:
        it = tqdm(
            it,
            total=graph.number_of_edges(),
            desc=f"Preparing TSV for {graph}",
            unit_scale=True,
            unit="edge",
        )

    triples = (to_triple(graph, u, v, key) for u, v, key in it)

    # clean duplicates and Nones
    rv = sorted({triple for triple in triples if triple is not None})
    if raise_on_none and not rv:
        raise NoTriplesValueError("Could not convert any triples")
    return rv


def to_triple(
    graph: BELGraph,
    u: BaseEntity,
    v: BaseEntity,
    key: str,
) -> tuple[str, str, str] | None:
    """Get the triples' strings that should be written to the file."""
    data = graph[u][v][key]

    # order is important
    _converters = [
        converters.ListComplexHasComponentConverter,
        converters.PartOfNamedComplexConverter,
        converters.SubprocessPartOfBiologicalProcessConverter,
        converters.ProteinPartOfBiologicalProcessConverter,
        converters.AbundancePartOfPopulationConverter,
        converters.PopulationPartOfAbundanceConverter,
        converters.RegulatesActivityConverter,
        converters.MiRNADecreasesExpressionConverter,
        converters.MiRNADirectlyDecreasesExpressionConverter,
        converters.AbundanceDirectlyDecreasesProteinActivityConverter,
        converters.AbundanceDirectlyIncreasesProteinActivityConverter,
        converters.IsAConverter,
        converters.EquivalenceConverter,
        converters.CorrelationConverter,
        converters.AssociationConverter,
        converters.DrugIndicationConverter,
        converters.DrugSideEffectConverter,
        converters.RegulatesAmountConverter,
        converters.ProcessCausalConverter,
        converters.IncreasesAmountConverter,
        converters.DecreasesAmountConverter,
        converters.NoChangeAmountConverter,
        converters.IncreasesActivityConverter,
        converters.DecreasesActivityConverter,
        converters.NoChangeActivityConverter,
        converters.ReactionHasProductConverter,
        converters.ReactionHasReactantConverter,
        converters.ReactionHasCatalystConverter,
        converters.HasVariantConverter,
        converters.IncreasesDegradationConverter,
        converters.DecreasesDegradationConverter,
        converters.RegulatesDegradationConverter,
        converters.NoChangeDegradationConverter,
        converters.TranscriptionFactorForConverter,
        converters.HomomultimerConverter,
        converters.BindsGeneConverter,
        converters.BindsProteinConverter,
        converters.ProteinRegulatesComplex,
    ]

    for converter in _converters:
        if converter.predicate(u, v, key, data):
            return converter.convert(u, v, key, data)

    logger.warning(f"unhandled: {graph.edge_to_bel(u, v, data)}")
