# -*- coding: utf-8 -*-

"""TSV converter classes."""

from abc import ABC, abstractmethod
from typing import Dict, Tuple

from ...constants import (
    ACTIVITY, ASSOCIATION, CAUSAL_DECREASE_RELATIONS, CAUSAL_INCREASE_RELATIONS, CAUSAL_RELATIONS, CAUSES_NO_CHANGE,
    CORRELATIVE_RELATIONS, DECREASES, DEGRADATION, DIRECTLY_DECREASES, DIRECTLY_INCREASES, EQUIVALENT_TO, HAS_PRODUCT,
    HAS_REACTANT, HAS_VARIANT, INCREASES, IS_A, MODIFIER, PART_OF, REGULATES, RELATION, TARGET_MODIFIER,
)
from ...dsl import (
    Abundance, BaseAbundance, BaseEntity, BiologicalProcess, CentralDogma, ComplexAbundance, Gene, MicroRna,
    NamedComplexAbundance, Pathology, Population, Protein, Reaction, Rna,
)
from ...typing import EdgeData


def _safe_label(base_entity: BaseEntity):
    return base_entity.safe_label


class Converter(ABC):
    """A condition and converter for a BEL edge."""

    @staticmethod
    @abstractmethod
    def predicate(u: BaseEntity, v: BaseEntity, key: str, edge_data: EdgeData) -> bool:
        """Test a BEL edge."""

    @staticmethod
    @abstractmethod
    def convert(u: BaseEntity, v: BaseEntity, key: str, edge_data: EdgeData) -> Tuple[str, str, str]:
        """Convert a BEL edge."""


class SimpleConverter(Converter):
    """A class for converting the source and target that have simple names."""

    @classmethod
    def convert(cls, u: BaseAbundance, v: BaseAbundance, key: str, edge_data: EdgeData) -> Tuple[str, str, str]:
        """Convert a BEL edge."""
        return u.safe_label, edge_data[RELATION], v.safe_label


class TypedConverter(Converter):
    """A class for converting the source and target but replaces the relation."""

    target_relation = None

    @classmethod
    def convert(cls, u: BaseAbundance, v: BaseAbundance, key: str, edge_data: EdgeData) -> Tuple[str, str, str]:
        """Convert a BEL edge."""
        return u.safe_label, cls.target_relation, v.safe_label


class SimplePredicate(Converter):
    """Converts BEL statements based on a given relation."""

    relation = ...

    @classmethod
    def predicate(cls, u, v, key, edge_data) -> bool:
        """Test a BEL edge has a given relation."""
        return edge_data[RELATION] == cls.relation


class SimpleTypedPredicate(SimplePredicate):
    """Finds BEL statements like ``A(X) B C(Y)`` where relation B and types A and C are defined in the class."""

    subject_type = ...
    object_type = ...

    @classmethod
    def predicate(cls, u: BaseEntity, v: BaseEntity, key: str, edge_data: EdgeData) -> bool:
        """Test a BEL edge."""
        return (
            super().predicate(u, v, key, edge_data)
            and isinstance(u, cls.subject_type)
            and isinstance(v, cls.object_type)
        )


class HasVariantConverter(SimpleConverter, SimpleTypedPredicate):
    """Converts BEL statements like ``p(X) hasVariant p(X, ...)``."""

    subject_type = CentralDogma
    relation = HAS_VARIANT
    object_type = CentralDogma


class _PartOfConverter(SimpleTypedPredicate, TypedConverter):
    relation = PART_OF
    target_relation = 'partOf'


class PartOfNamedComplexConverter(_PartOfConverter):
    """Converts BEL statements like ``p(X) partOf complex(Y)``."""

    subject_type = Protein
    object_type = NamedComplexAbundance


class ProcessCausalConverter(SimpleConverter, SimpleTypedPredicate):
    """Converts BEL statements like ``bp(X) increases/decreases bp(Y)``."""

    subject_type = BiologicalProcess
    relations = CAUSAL_RELATIONS
    object_type = BiologicalProcess

    @classmethod
    def predicate(cls, u, v, key, edge_data) -> bool:
        """Test a BEL edge has a given relation."""
        return (
            isinstance(u, cls.subject_type)
            and edge_data[RELATION] in cls.relations
            and isinstance(v, cls.object_type)
        )


class SubprocessPartOfBiologicalProcessConverter(_PartOfConverter):
    """Converts BEL statements like ``bp(X) partOf bp(Y)``."""

    subject_type = BiologicalProcess
    object_type = BiologicalProcess


class ProteinPartOfBiologicalProcessConverter(_PartOfConverter):
    """Converts BEL statements like ``p(X) partOf bp(Y)``."""

    subject_type = Protein
    object_type = BiologicalProcess


class AbundancePartOfPopulationConverter(_PartOfConverter):
    """Converts BEL statements like ``a(X) partOf pop(Y)``."""

    subject_type = Abundance
    object_type = Population


class PopulationPartOfAbundanceConverter(_PartOfConverter):
    """Converts BEL statements like ``pop(X) partOf a(Y)``."""

    subject_type = Population
    object_type = Abundance


class _ReactionTypedPredicate(SimpleTypedPredicate):
    subject_type = Reaction
    object_type = BaseAbundance


class _ReactionHasMemberConverter(_ReactionTypedPredicate):
    """Converts BEL statements like ``complex(X) hasComponent p(Y)``."""

    target_relation = ...

    @classmethod
    def predicate(cls, u: Reaction, v: BaseAbundance, key: str, edge_data: EdgeData) -> bool:
        """Test a BEL edge."""
        return super().predicate(u, v, key, edge_data) and v not in u.get_catalysts()

    @classmethod
    def convert(cls, u: Reaction, v: BaseAbundance, key: str, data: Dict) -> Tuple[str, str, str]:
        """Convert a BEL edge."""
        return u.as_bel(), cls.target_relation, v.curie


class ReactionHasReactantConverter(_ReactionHasMemberConverter):
    """Converts BEL statements like ``rxn(X) hasReactant a(Y)``."""

    relation = HAS_REACTANT
    target_relation = 'hasReactant'


class ReactionHasProductConverter(_ReactionHasMemberConverter):
    """Converts BEL statements like ``rxn(X) hasProduct a(Y)``."""

    relation = HAS_PRODUCT
    target_relation = 'hasProduct'


class ReactionHasCatalystConverter(_ReactionTypedPredicate):
    """Converts BEL statements that simultaneously ``rxn(X) hasProduct a(Y)`` and ``rxn(X) hasReactant a(Y)``."""

    target_relation = 'hasCatalyst'

    @classmethod
    def predicate(cls, u: Reaction, v: BaseAbundance, key: str, edge_data: EdgeData) -> bool:
        """Test a BEL edge."""
        return super().predicate(u, v, key, edge_data) and v in u.get_catalysts()

    @classmethod
    def convert(cls, u: Reaction, v: BaseAbundance, key: str, data: Dict) -> Tuple[str, str, str]:
        """Convert a BEL edge."""
        return u.as_bel(), cls.target_relation, v.curie


class ListComplexHasComponentConverter(SimpleTypedPredicate):
    """Converts BEL statements like ``complex(p(X), p(Y), ...) hasComponent p(X)``."""

    subject_type = BaseAbundance
    relation = PART_OF
    object_type = ComplexAbundance
    target_relation = 'partOf'

    @classmethod
    def convert(cls, u: ComplexAbundance, v: BaseAbundance, key: str, data: Dict) -> Tuple[str, str, str]:
        """Convert a BEL edge."""
        return u.curie, cls.target_relation, v.as_bel()


class IsAConverter(SimplePredicate, SimpleConverter):
    """Converts BEL statements like ``X isA Y``."""

    relation = IS_A
    target_relation = 'isA'


class EquivalenceConverter(SimplePredicate, SimpleConverter):
    """Converts BEL statements like ``X eq Y``."""

    relation = EQUIVALENT_TO
    target_relation = 'equivalentTo'


class CorrelationConverter(SimpleConverter):
    """Converts BEL statements like ``A(B) pos|neg|noCorrelation C(D)``."""

    @staticmethod
    def predicate(u: BaseEntity, v: BaseEntity, key: str, edge_data: EdgeData) -> bool:
        """Test a BEL edge."""
        return edge_data[RELATION] in CORRELATIVE_RELATIONS


class AssociationConverter(Converter):
    """Converts BEL statements like ``a(X) -- path(Y)``."""

    @staticmethod
    def predicate(u: BaseEntity, v: BaseEntity, key: str, edge_data: EdgeData) -> bool:
        """Test a BEL edge."""
        return edge_data[RELATION] == ASSOCIATION

    @staticmethod
    def convert(u: BaseAbundance, v: BaseAbundance, key: str, edge_data: EdgeData) -> Tuple[str, str, str]:
        """Convert a BEL edge."""
        relation = edge_data.get('association_type', ASSOCIATION)  # allow more specific association to be defined
        return u.safe_label, relation, v.safe_label


class DrugEffectConverter(SimpleConverter, SimpleTypedPredicate):
    """Converts BEL statements like ``a(X) ? path(Y)``."""

    subject_type = Abundance
    relation = ...
    object_type = Pathology


class DrugIndicationConverter(DrugEffectConverter):
    """Converts BEL statements like ``a(X) -| path(Y)``."""

    relation = DECREASES


class DrugSideEffectConverter(DrugEffectConverter):
    """Converts BEL statements like ``a(X) -> path(Y)``."""

    relation = INCREASES


class RegulatesAmountConverter(TypedConverter):
    """Converts BEL statements like ``A(B) reg C(D)``."""

    relation = REGULATES
    target_relation = 'regulatesAmountOf'

    @classmethod
    def predicate(cls, u: BaseEntity, v: BaseEntity, key: str, edge_data: EdgeData) -> bool:
        """Test a BEL edge."""
        target_modifier = edge_data.get(TARGET_MODIFIER)
        return edge_data[RELATION] == cls.relation and (not target_modifier or not target_modifier.get(MODIFIER))


class IncreasesAmountConverter(RegulatesAmountConverter):
    """Converts BEL statements like ``A(B) -> C(D)``."""

    relation = INCREASES
    target_relation = 'increasesAmountOf'


class DecreasesAmountConverter(RegulatesAmountConverter):
    """Converts BEL statements like ``A(B) -| C(D)``."""

    relation = DECREASES
    target_relation = 'decreasesAmountOf'


class NoChangeAmountConverter(RegulatesAmountConverter):
    """Converts BEL statements like ``A(B) cnc C(D)``."""

    relation = CAUSES_NO_CHANGE
    target_relation = 'notRegulatesAmountOf'


class RegulatesDegradationConverter(TypedConverter):
    """Converts BEL statements like ``A(B) reg deg(C(D))``."""

    relation = REGULATES
    target_relation = 'regulatesAmountOf'

    @classmethod
    def predicate(cls, u: BaseEntity, v: BaseEntity, key: str, edge_data: EdgeData) -> bool:
        """Test a BEL edge."""
        target_modifier = edge_data.get(TARGET_MODIFIER)
        return (
            edge_data[RELATION] == cls.relation
            and target_modifier
            and target_modifier.get(MODIFIER) == DEGRADATION
        )


class IncreasesDegradationConverter(RegulatesDegradationConverter):
    """Converts BEL statements like ``A(B) -> deg(C(D))``."""

    relation = INCREASES
    target_relation = 'decreasesAmountOf'


class DecreasesDegradationConverter(RegulatesDegradationConverter):
    """Converts BEL statements like ``A(B) -| deg(C(D))``."""

    relation = DECREASES
    target_relation = 'increasesAmountOf'


class NoChangeDegradationConverter(RegulatesDegradationConverter):
    """Converts BEL statements like ``A(B) cnc deg(C(D))``."""

    relation = CAUSES_NO_CHANGE
    target_relation = 'notRegulatesAmountOf'


class RegulatesActivityConverter(TypedConverter):
    """Converts BEL statements like ``A(B) reg act(C(D) [, ma(E)])``."""

    relation = REGULATES
    target_relation = 'activityDirectlyRegulatesActivityOf'

    @classmethod
    def predicate(cls, u: BaseEntity, v: BaseEntity, key: str, edge_data: EdgeData) -> bool:
        """Test a BEL edge."""
        target_modifier = edge_data.get(TARGET_MODIFIER)
        return (
            edge_data[RELATION] == cls.relation
            and target_modifier
            and target_modifier.get(MODIFIER) == ACTIVITY
        )


class IncreasesActivityConverter(RegulatesActivityConverter):
    """Converts BEL statements like ``A(B) -> act(C(D) [, ma(E)])``."""

    relation = INCREASES
    target_relation = 'activityPositivelyRegulatesActivityOf'


class DirectlyIncreasesActivityConverter(RegulatesActivityConverter):
    """Converts BEL statements like ``A(B) => act(C(D) [, ma(E)])``."""

    relation = DIRECTLY_INCREASES
    target_relation = 'activityDirectlyPositivelyRegulatesActivityOf'


class DecreasesActivityConverter(RegulatesActivityConverter):
    """Converts BEL statements like ``A(B) -| act(C(D) [, ma(E)])``."""

    relation = DECREASES
    target_relation = 'activityNegativelyRegulatesActivityOf'


class DirectlyDecreasesActivityConverter(RegulatesActivityConverter):
    """Converts BEL statements like ``A(B) =| act(C(D) [, ma(E)])``."""

    relation = DIRECTLY_DECREASES
    target_relation = 'activityDirectlyNegativelyRegulatesActivityOf'


class NoChangeActivityConverter(RegulatesActivityConverter):
    """Converts BEL statements like ``A(B) cnc act(C(D) [, ma(E)])``."""

    relation = CAUSES_NO_CHANGE
    target_relation = 'notActivityDirectlyRegulatesActivityOf'


class AbundanceDirectlyDecreasesProteinActivityConverter(DirectlyDecreasesActivityConverter):
    """Converts BEL statements like ``a(X) =| act(p(Y))``."""

    subject_type = Abundance
    object_type = Protein


class AbundanceDirectlyIncreasesProteinActivityConverter(DirectlyIncreasesActivityConverter):
    """Converts BEL statements like ``a(X) => act(p(Y))``."""

    subject_type = Abundance
    object_type = Protein


class MiRNARegulatesExpressionConverter(TypedConverter, SimpleTypedPredicate):
    """Converts BEL statements like ``m(X) reg r(Y)``."""

    subject_type = MicroRna
    relation = REGULATES
    object_type = Rna
    target_relation = 'regulatesExpressionOf'


class MiRNAIncreasesExpressionConverter(MiRNARegulatesExpressionConverter):
    """Converts BEL statements like ``m(X) -> r(Y)``."""

    relation = INCREASES
    target_relation = 'increasesExpressionOf'


class MiRNADirectlyIncreasesExpressionConverter(MiRNARegulatesExpressionConverter):
    """Converts BEL statements like ``m(X) => r(Y)``."""

    relation = DIRECTLY_INCREASES
    target_relation = 'increasesExpressionOf'


class MiRNADecreasesExpressionConverter(MiRNARegulatesExpressionConverter):
    """Converts BEL statements like ``m(X) -| r(Y)``."""

    relation = DECREASES
    target_relation = 'repressesExpressionOf'


class MiRNADirectlyDecreasesExpressionConverter(MiRNARegulatesExpressionConverter):
    """Converts BEL statements like ``m(X) =| r(Y)``."""

    relation = DIRECTLY_DECREASES
    target_relation = 'repressesExpressionOf'


class TranscriptionFactorForConverter(Converter):
    """Converts ``complex(g(A), p(B)) directlyIncreases r(A)```."""

    @classmethod
    def convert(cls, u: BaseEntity, v: BaseEntity, key: str, edge_data: EdgeData) -> Tuple[str, str, str]:
        """Convert a transcription factor for edge."""
        gene = v.get_gene()
        if gene == u.members[0]:
            return u.members[1].safe_label, edge_data[RELATION], v.safe_label
        else:
            return u.members[0].safe_label, edge_data[RELATION], v.safe_label

    @classmethod
    def predicate(cls, u: BaseEntity, v: BaseEntity, key: str, edge_data: EdgeData) -> bool:
        """Test a BEL edge."""
        if not isinstance(u, ComplexAbundance) or len(u.members) != 2:
            return False

        if isinstance(u.members[0], Gene) and isinstance(u.members[1], Protein):
            gene = u.members[0]
        elif isinstance(u.members[1], Gene) and isinstance(u.members[0], Protein):
            gene = u.members[1]
        else:
            return False

        if not isinstance(v, Rna):
            return False

        return gene == v.get_gene()


class BindsProteinConverter(Converter):
    """Converts ``x(B) => complex(p(A), x(B))```."""

    @staticmethod
    def predicate(u: BaseEntity, v: BaseEntity, key: str, edge_data: EdgeData) -> bool:
        """Test a BEL edge."""
        return (
            edge_data[RELATION] == DIRECTLY_INCREASES
            and isinstance(v, ComplexAbundance)
            and len(v.members) == 2
            and u in v.members
            and isinstance([m for m in v.members if m != u][0], Protein)
        )

    @staticmethod
    def convert(u: BaseEntity, v: BaseEntity, key: str, edge_data: EdgeData) -> Tuple[str, str, str]:
        """Convert a binds protein factor for edge."""
        v = [m for m in v.members if m != u][0]
        return u.safe_label, 'bindsToProtein', v.safe_label


class HomomultimerConverter(Converter):
    """Converts ``p(A) directlyIncreases complex(p(A), p(A))```."""

    @staticmethod
    def predicate(u: BaseEntity, v: BaseEntity, key: str, edge_data: EdgeData) -> bool:
        """Test a BEL edge."""
        return (
            isinstance(u, Protein)
            and edge_data[RELATION] == DIRECTLY_INCREASES
            and isinstance(v, ComplexAbundance)
            and all(member == u for member in v.members)
        )

    @staticmethod
    def convert(u: BaseEntity, v: BaseEntity, key: str, edge_data: EdgeData) -> Tuple[str, str, str]:
        """Convert a homomultimer formation."""
        return u.safe_label, 'bindsToProtein', u.safe_label


class BindsGeneConverter(Converter):
    """Converts ``p(B) directlyIncreases complex(g(A), p(B))```."""

    @staticmethod
    def predicate(u: BaseEntity, v: BaseEntity, key: str, edge_data: EdgeData) -> bool:
        """Test a BEL edge."""
        return (
            isinstance(u, Protein)
            and edge_data[RELATION] == DIRECTLY_INCREASES
            and isinstance(v, ComplexAbundance)
            and len(v.members) == 2
            and u in v.members
            and isinstance([m for m in v.members if m != u][0], Gene)
        )

    @staticmethod
    def convert(u: BaseEntity, v: BaseEntity, key: str, edge_data: EdgeData) -> Tuple[str, str, str]:
        """Convert a transcription factor for edge."""
        v = [m for m in v.members if m != u][0]
        return u.safe_label, 'bindsToGene', v.safe_label


class ProteinRegulatesComplex(Converter):
    """Converts ``p(B) directlyIncreases complex(x(X), y(Y))```."""

    @staticmethod
    def predicate(u: BaseEntity, v: BaseEntity, key: str, edge_data: EdgeData) -> bool:
        """Test a BEL edge."""
        return (
            isinstance(u, Protein)
            and isinstance(v, ComplexAbundance)
            and u not in v.members
            and edge_data[RELATION] in CAUSAL_RELATIONS
            and edge_data[RELATION] != CAUSES_NO_CHANGE
        )

    @staticmethod
    def convert(u: BaseEntity, v: BaseEntity, key: str, edge_data: EdgeData) -> Tuple[str, str, str]:
        """Convert a transcription factor for edge."""
        relation = edge_data[RELATION]
        if relation in CAUSAL_INCREASE_RELATIONS:
            relation = 'increasesAmountOf'
        elif relation in CAUSAL_DECREASE_RELATIONS:
            relation = 'decreasesAmountOf'
        elif relation == REGULATES:
            relation = 'regulatesAmountOf'
        else:
            raise ValueError('invalid relation type')

        return u.safe_label, relation, v.safe_label
