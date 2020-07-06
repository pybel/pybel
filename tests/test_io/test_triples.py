# -*- coding: utf-8 -*-

"""Tests for the conversion procedure."""

import unittest
from typing import Tuple, Type

from pybel import BELGraph
from pybel.constants import (
    ASSOCIATION, DECREASES, DIRECTLY_DECREASES, DIRECTLY_INCREASES, EQUIVALENT_TO, INCREASES, IS_A,
    NEGATIVE_CORRELATION, TARGET_MODIFIER, PART_OF, POSITIVE_CORRELATION, REGULATES, RELATION,
)
from pybel.dsl import (
    Abundance, BaseEntity, BiologicalProcess, ComplexAbundance, MicroRna, NamedComplexAbundance, Pathology,
    Population, Protein, Rna, activity,
)
from pybel.io.triples import converters as tsvc
from pybel.io.triples.api import to_triple
from pybel.io.triples.converters import (
    AbundanceDirectlyDecreasesProteinActivityConverter, AbundanceDirectlyIncreasesProteinActivityConverter,
    AbundancePartOfPopulationConverter, AssociationConverter, Converter, CorrelationConverter, DecreasesAmountConverter,
    DrugIndicationConverter, DrugSideEffectConverter, EquivalenceConverter, IncreasesAmountConverter, IsAConverter,
    MiRNADecreasesExpressionConverter, PartOfNamedComplexConverter, RegulatesActivityConverter,
    RegulatesAmountConverter, SubprocessPartOfBiologicalProcessConverter, TranscriptionFactorForConverter,
)
from pybel.testing.utils import n
from pybel.typing import EdgeData


def _rel(x):
    return {RELATION: x}


def _rela(x, y=None):
    return {RELATION: x, TARGET_MODIFIER: activity(y)}


def _assoc(y):
    return {RELATION: ASSOCIATION, 'association_type': y}


a1 = Abundance('CHEBI', '1')
p1 = Protein('HGNC', '1')
pf1 = Protein('INTERPRO', '1')
d1 = Pathology('MESH', '1')
b1 = BiologicalProcess('GO', '1')
b2 = BiologicalProcess('GO', '2')
m1 = MicroRna('MIRBASE', '1')
r1 = Rna('HGNC', '1')
r2 = Rna('HGNC', '2')
nca1 = NamedComplexAbundance('FPLX', '1')
pop1 = Population('taxonomy', '1')

p2 = Protein('HGNC', identifier='9236')
p3 = Protein('HGNC', identifier='9212')
r3 = p3.get_rna()
g3 = r3.get_gene()

c1 = ComplexAbundance([p2, g3])
c2 = ComplexAbundance([p1, p2])
c3 = ComplexAbundance([a1, p2])
p1_homodimer = ComplexAbundance([p1, p1])
p1_homotrimer = ComplexAbundance([p1, p1, p1])

converters_true_list = [
    (PartOfNamedComplexConverter, p1, nca1, _rel(PART_OF), ('HGNC:1', 'partOf', 'FPLX:1')),
    (SubprocessPartOfBiologicalProcessConverter, b1, b2, _rel(PART_OF), ('GO:1', 'partOf', 'GO:2')),
    (tsvc.ProcessCausalConverter, b1, b2, _rel(INCREASES), ('GO:1', INCREASES, 'GO:2')),
    (tsvc.ProcessCausalConverter, b1, b2, _rel(DECREASES), ('GO:1', DECREASES, 'GO:2')),
    (tsvc.ProcessCausalConverter, b1, b2, _rel(DIRECTLY_INCREASES), ('GO:1', DIRECTLY_INCREASES, 'GO:2')),
    (tsvc.ProcessCausalConverter, b1, b2, _rel(DIRECTLY_DECREASES), ('GO:1', DIRECTLY_DECREASES, 'GO:2')),
    (AssociationConverter, r1, r2, _rel(ASSOCIATION), ('HGNC:1', 'association', 'HGNC:2')),
    (AssociationConverter, r1, r2, _assoc('similarity'), ('HGNC:1', 'similarity', 'HGNC:2')),
    (CorrelationConverter, r1, r2, _rel(POSITIVE_CORRELATION), ('HGNC:1', 'positiveCorrelation', 'HGNC:2')),
    (IsAConverter, p1, pf1, _rel(IS_A), ('HGNC:1', 'isA', 'INTERPRO:1')),
    # Found in ADEPTUS
    (CorrelationConverter, d1, r1, _rel(POSITIVE_CORRELATION), ('MESH:1', 'positiveCorrelation', 'HGNC:1')),
    (CorrelationConverter, d1, r1, _rel(NEGATIVE_CORRELATION), ('MESH:1', 'negativeCorrelation', 'HGNC:1')),
    # Found in LINCS (not integrated yet)
    (RegulatesAmountConverter, a1, r1, _rel(REGULATES), ('CHEBI:1', 'regulatesAmountOf', 'HGNC:1')),
    (IncreasesAmountConverter, a1, r1, _rel(INCREASES), ('CHEBI:1', 'increasesAmountOf', 'HGNC:1')),
    (DecreasesAmountConverter, a1, r1, _rel(DECREASES), ('CHEBI:1', 'decreasesAmountOf', 'HGNC:1')),
    # Found in SIDER
    (DrugSideEffectConverter, a1, d1, _rel(INCREASES), ('CHEBI:1', 'increases', 'MESH:1')),
    (DrugIndicationConverter, a1, d1, _rel(DECREASES), ('CHEBI:1', 'decreases', 'MESH:1')),
    # Found in miRTarBase
    (MiRNADecreasesExpressionConverter, m1, r1, _rel(DECREASES), ('MIRBASE:1', 'repressesExpressionOf', 'HGNC:1')),
    # Found in chemogenomics databases (e.g., DrugBank)
    (
        RegulatesActivityConverter, a1, p1, _rela(REGULATES),
        ('CHEBI:1', 'activityDirectlyRegulatesActivityOf', 'HGNC:1'),
    ),
    (
        AbundanceDirectlyDecreasesProteinActivityConverter, a1, p1, _rela(DIRECTLY_DECREASES),
        ('CHEBI:1', 'activityDirectlyNegativelyRegulatesActivityOf', 'HGNC:1'),
    ),
    (
        AbundanceDirectlyIncreasesProteinActivityConverter, a1, p1, _rela(DIRECTLY_INCREASES),
        ('CHEBI:1', 'activityDirectlyPositivelyRegulatesActivityOf', 'HGNC:1'),
    ),
    # Found in ComPath
    (EquivalenceConverter, b1, b2, _rel(EQUIVALENT_TO), ('GO:1', 'equivalentTo', 'GO:2')),
    (SubprocessPartOfBiologicalProcessConverter, b1, b2, _rel(PART_OF), ('GO:1', 'partOf', 'GO:2')),
    # Misc
    (AbundancePartOfPopulationConverter, a1, pop1, _rel(PART_OF), ('CHEBI:1', 'partOf', 'taxonomy:1')),
    # complex(g(hgnc:9212), p(hgnc:9236)) directlyIncreases r(hgnc:9212)
    (
        TranscriptionFactorForConverter, c1, r3, _rel(DIRECTLY_INCREASES),
        ('HGNC:9236', DIRECTLY_INCREASES, 'HGNC:9212'),
    ),
    (
        TranscriptionFactorForConverter, c1, r3, _rel(DIRECTLY_DECREASES),
        ('HGNC:9236', DIRECTLY_DECREASES, 'HGNC:9212'),
    ),
    (
        tsvc.BindsGeneConverter, p2, c1, _rel(DIRECTLY_INCREASES),
        (p2.curie, 'bindsToGene', g3.curie),
    ),
    (
        tsvc.BindsProteinConverter, p1, c2, _rel(DIRECTLY_INCREASES),
        (p1.curie, 'bindsToProtein', p2.curie),
    ),
    (
        tsvc.BindsProteinConverter, a1, c3, _rel(DIRECTLY_INCREASES),
        (a1.curie, 'bindsToProtein', p2.curie),
    ),
    (
        tsvc.HomomultimerConverter, p1, p1_homodimer, _rel(DIRECTLY_INCREASES),
        (p1.curie, 'bindsToProtein', p1.curie),
    ),
    (
        tsvc.HomomultimerConverter, p1, p1_homotrimer, _rel(DIRECTLY_INCREASES),
        (p1.curie, 'bindsToProtein', p1.curie),
    ),
    (
        tsvc.ProteinRegulatesComplex, p3, c2, _rel(DIRECTLY_INCREASES),
        (p3.curie, 'increasesAmountOf', str(c2)),
    ),
    (
        tsvc.ProteinRegulatesComplex, p3, c2, _rel(DIRECTLY_DECREASES),
        (p3.curie, 'decreasesAmountOf', str(c2)),
    ),
    (
        tsvc.ProteinRegulatesComplex, p3, c2, _rel(DECREASES),
        (p3.curie, 'decreasesAmountOf', str(c2)),
    ),
    (
        tsvc.ProteinRegulatesComplex, p3, c2, _rel(INCREASES),
        (p3.curie, 'increasesAmountOf', str(c2)),
    ),
]

converters_false_list = [
    (PartOfNamedComplexConverter, nca1, p1, _rel(IS_A)),
]


class TestConverters(unittest.TestCase):
    """Tests for the converter classes."""

    def help_test_convert(
        self,
        converter: Type[Converter],
        u: BaseEntity,
        v: BaseEntity,
        edge_data: EdgeData,
        triple: Tuple[str, str, str],
    ) -> None:
        """Test a converter class."""
        self.assertTrue(issubclass(converter, Converter), msg='Not a Converter: {}'.format(converter.__name__))
        key = n()
        self.assertTrue(
            converter.predicate(u, v, key, edge_data),
            msg='Predicate failed: {}'.format(converter.__name__),
        )
        self.assertEqual(
            triple,
            converter.convert(u, v, key, edge_data),
            msg='Conversion failed: {}'.format(converter.__name__),
        )
        graph = BELGraph()
        graph.add_edge(u, v, key=key, **edge_data)
        self.assertEqual(
            triple,
            to_triple(graph, u, v, key),
            msg='get_triple failed: {}'.format(converter.__name__),
        )

    def test_converters_true(self):
        """Test passing converters."""
        for converter, u, v, edge_data, triple in converters_true_list:
            with self.subTest(converter=converter.__qualname__):
                self.help_test_convert(converter, u, v, edge_data, triple)

    def test_converters_false(self):
        """Test falsification of converters."""
        for converter, u, v, edge_data in converters_false_list:
            with self.subTest(converter=converter.__qualname__):
                self.assertFalse(converter.predicate(u, v, n(), edge_data))
