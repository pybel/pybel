# -*- coding: utf-8 -*-

"""Classes for DSL nodes."""

import hashlib
from abc import ABCMeta, abstractmethod
from operator import methodcaller
from typing import Iterable, List, Optional, Set, Union

from .exc import InferCentralDogmaException, ListAbundanceEmptyException, ReactionEmptyException
from ..constants import (
    ABUNDANCE, BEL_DEFAULT_NAMESPACE, BIOPROCESS, COMPLEX, COMPOSITE, CONCEPT, FRAGMENT, FRAGMENT_DESCRIPTION,
    FRAGMENT_MISSING, FRAGMENT_START, FRAGMENT_STOP, FUNCTION, FUSION, FUSION_MISSING, FUSION_REFERENCE, FUSION_START,
    FUSION_STOP, GENE, GMOD, HGVS, KIND, MEMBERS, MIRNA, PARTNER_3P, PARTNER_5P, PATHOLOGY, PMOD, PMOD_CODE, PMOD_ORDER,
    PMOD_POSITION, POPULATION, PRODUCTS, PROTEIN, RANGE_3P, RANGE_5P, REACTANTS, REACTION, RNA, VARIANTS, XREFS,
    rev_abundance_labels,
)
from ..language import Entity

__all__ = [
    'Abundance',

    # Central Dogma Stuff
    'Gene',
    'Rna',
    'MicroRna',
    'Protein',

    # Fusions
    'ProteinFusion',
    'RnaFusion',
    'GeneFusion',

    # Fusion Ranges
    'EnumeratedFusionRange',
    'MissingFusionRange',

    # Transformations
    'ComplexAbundance',
    'CompositeAbundance',
    'BiologicalProcess',
    'Pathology',
    'Population',
    'NamedComplexAbundance',
    'Reaction',

    # Variants
    'ProteinModification',
    'GeneModification',
    'Hgvs',
    'HgvsReference',
    'HgvsUnspecified',
    'ProteinSubstitution',
    'Fragment',

    # Base Classes
    'Entity',
    'BaseEntity',
    'BaseAbundance',
    'CentralDogma',
    'ListAbundance',
    'Variant',
    'FusionBase',
    'FusionRangeBase',
]

# A methodcaller for the key argument of sorted()
_as_bel = methodcaller('as_bel')


class BaseEntity(dict, metaclass=ABCMeta):
    """This class represents all BEL nodes.

    It can be converted to a tuple and hashed.
    """

    function = ...

    def __init__(self) -> None:
        """Build a PyBEL node."""
        super().__init__(**{FUNCTION: self.function})
        self._md5 = None

    @property
    def _bel_function(self) -> str:
        return rev_abundance_labels[self.function]

    @abstractmethod
    def as_bel(self, use_identifiers: bool = True) -> str:
        """Return this entity as a BEL string."""

    @property
    def md5(self) -> str:
        """Get the MD5 hash of this node."""
        if self._md5 is None:
            self._md5 = hashlib.md5(self.as_bel().encode('utf8')).hexdigest()  # noqa: S303
        return self._md5

    def __hash__(self):  # noqa: D105
        return hash(self.as_bel())

    def __eq__(self, other):
        return isinstance(other, BaseEntity) and self.as_bel() == other.as_bel()

    def __repr__(self):
        return '<BEL {bel}>'.format(bel=self.as_bel(use_identifiers=True))

    def __str__(self):  # noqa: D105
        return self.as_bel()


class BaseAbundance(BaseEntity):
    """The superclass for building node data dictionaries.

    This class must be subclassed and the class variable `function` must be
    overridden.
    """

    def __init__(
        self,
        namespace: str,
        name: Optional[str] = None,
        identifier: Optional[str] = None,
        xrefs: Optional[List[Entity]] = None,
    ) -> None:
        """Build an abundance from a function, namespace, and a name and/or identifier.

        :param namespace: The name of the namespace
        :param name: The name of this abundance
        :param identifier: The database identifier for this abundance
        :param xrefs: Alternate identifiers for the entity
        """
        super().__init__()
        self[CONCEPT] = Entity(
            namespace=namespace,
            name=name,
            identifier=identifier,
        )
        if xrefs:
            self[XREFS] = xrefs

    @property
    def entity(self) -> Entity:  # noqa:D401
        """This node's concept."""
        return self[CONCEPT]

    @property
    def xrefs(self) -> List[Entity]:  # noqa:D401
        """Alternative identifiers for the node's concept."""
        return self.get(XREFS, [])

    @property
    def namespace(self) -> str:  # noqa:D401
        """The namespace of this abundance."""
        return self.entity.namespace

    @property
    def name(self) -> Optional[str]:  # noqa:D401
        """The name of this abundance."""
        return self.entity.name

    @property
    def identifier(self) -> Optional[str]:  # noqa:D401
        """The identifier of this abundance."""
        return self.entity.identifier

    @property
    def curie(self):  # noqa: D401
        """The CURIE-style identifier for this node."""
        return self.entity.curie

    @property
    def obo(self) -> str:  # noqa: D401
        """The OBO-style identifier for this node."""
        return self.entity.obo

    def as_bel(self, use_identifiers: bool = True) -> str:
        """Return this node as a BEL string."""
        return "{}({})".format(
            self._bel_function,
            self.obo if use_identifiers and self.entity.identifier and self.entity.name else self.curie,
        )


class Abundance(BaseAbundance):
    """Builds an abundance node.

    Example:
    >>> Abundance(namespace='CHEBI', name='water')

    """

    function = ABUNDANCE


class BiologicalProcess(BaseAbundance):
    """Builds a biological process node.

    Example:
    >>> BiologicalProcess(namespace='GO', name='apoptosis')

    """

    function = BIOPROCESS


class Pathology(BaseAbundance):
    """Build a pathology node.

    Example:
    >>> Pathology(namespace='DO', name='Alzheimer Disease')

    """

    function = PATHOLOGY


class Population(BaseAbundance):
    """Builds a popuation node.

    Example:
    >>> Population(namespace='uberon', name='blood')

    """

    function = POPULATION


class Variant(dict, metaclass=ABCMeta):
    """The superclass for variant dictionaries."""

    def __init__(self, kind: str) -> None:
        """Build the variant data dictionary.

        :param kind: The kind of variant
        """
        super().__init__({KIND: kind})

    @abstractmethod
    def as_bel(self, use_identifiers: bool = True) -> str:
        """Return this variant as a BEL string."""

    def __str__(self):  # noqa: D105
        return self.as_bel()


class CentralDogma(BaseAbundance):
    """The base class for "central dogma" abundances (i.e., genes, miRNAs, RNAs, and proteins)."""

    def __init__(
        self,
        namespace: str,
        name: Optional[str] = None,
        identifier: Optional[str] = None,
        xrefs: Optional[List[Entity]] = None,
        variants: Union[None, Variant, Iterable[Variant]] = None,
    ) -> None:
        """Build a node for a gene, RNA, miRNA, or protein.

        :param namespace: The name of the database used to identify this entity
        :param name: The database's preferred name or label for this entity
        :param identifier: The database's identifier for this entity
        :param xrefs: Alternative database cross references
        :param variants: An optional variant or list of variants
        """
        super().__init__(namespace=namespace, name=name, identifier=identifier, xrefs=xrefs)

        if isinstance(variants, Variant):
            self[VARIANTS] = [variants]
        elif isinstance(variants, (list, tuple, set)):
            self[VARIANTS] = sorted(variants, key=_as_bel)

    @property
    def variants(self) -> Optional[List[Variant]]:
        """Return this entity's variants, if they exist."""
        return self.get(VARIANTS)

    def as_bel(self, use_identifiers: bool = True) -> str:
        """Return this node as a BEL string."""
        if not self.variants:
            return super().as_bel(use_identifiers=use_identifiers)

        variants_canon = sorted([
            variant.as_bel(use_identifiers=use_identifiers)
            for variant in self.variants
        ])

        return "{}({}, {})".format(
            self._bel_function,
            self.obo if use_identifiers and self.entity.identifier and self.entity.name else self.curie,
            ', '.join(variants_canon),
        )

    def get_parent(self) -> Optional['CentralDogma']:
        """Get the parent, or none if it's already a reference node.

        Example usage:

        >>> ab42 = Protein(name='APP', namespace='HGNC', variants=[Fragment(start=672, stop=713)])
        >>> app = ab42.get_parent()
        >>> assert 'p(HGNC:APP)' == app.as_bel()

        """
        if VARIANTS not in self:
            return None

        return self.__class__(
            namespace=self.namespace,
            name=self.name,
            identifier=self.identifier,
            xrefs=self.xrefs,
        )

    def with_variants(self, variants: Union[Variant, List[Variant]]) -> 'CentralDogma':
        """Create a new entity with the given variants.

        :param variants: An optional variant or list of variants

        Example Usage:

        >>> app = Protein(name='APP', namespace='HGNC')
        >>> ab42 = app.with_variants([Fragment(start=672, stop=713)])
        >>> assert 'p(HGNC:APP, frag(672_713))' == ab42.as_bel()

        """
        return self.__class__(
            namespace=self.namespace,
            name=self.name,
            identifier=self.identifier,
            xrefs=self.xrefs,
            variants=variants,
        )


class ProteinModification(Variant):
    """Build a protein modification variant dictionary."""

    def __init__(
        self,
        name: str,
        code: Optional[str] = None,
        position: Optional[int] = None,
        namespace: Optional[str] = None,
        identifier: Optional[str] = None,
        xrefs: Optional[List[Entity]] = None,
    ) -> None:
        """Build a protein modification variant data dictionary.

        :param name: The name of the modification
        :param code: The three letter amino acid code for the affected residue. Capital first letter.
        :param position: The position of the affected residue
        :param namespace: The namespace to which the name of this modification belongs
        :param identifier: The identifier of the name of the modification
        :param xrefs: Alternative database xrefs

        Either the name or the identifier must be used. If the namespace is omitted, it is assumed that a name is
        specified from the BEL default namespace.

        Example from BEL default namespace:

        >>> ProteinModification('Ph', code='Thr', position=308)

        Example from custom namespace:

        >>> ProteinModification(name='protein phosphorylation', namespace='GO', code='Thr', position=308)

        Example from custom namespace additionally qualified with identifier:

        >>> ProteinModification(name='protein phosphorylation', namespace='GO',
        >>>                     identifier='GO:0006468', code='Thr', position=308)

        """
        super().__init__(kind=PMOD)

        self[CONCEPT] = Entity(
            namespace=(namespace or BEL_DEFAULT_NAMESPACE),
            name=name,
            identifier=identifier,
        )
        if xrefs:
            self['xref'] = xrefs

        if code:
            self[PMOD_CODE] = code

        if position:
            self[PMOD_POSITION] = position

    @property
    def entity(self) -> Entity:  # noqa:D401
        """The concept for this protein modification."""
        return self[CONCEPT]

    def as_bel(self, use_identifiers: bool = True) -> str:
        """Return this protein modification variant as a BEL string."""
        if use_identifiers and self.entity.identifier and self.entity.name:
            x = self.entity.obo
        else:
            x = self.entity.curie

        return 'pmod({}{})'.format(
            x,
            ''.join(', {}'.format(self[x]) for x in PMOD_ORDER[2:] if x in self),
        )


class GeneModification(Variant):
    """Build a gene modification variant dictionary."""

    def __init__(
        self,
        name: str,
        namespace: Optional[str] = None,
        identifier: Optional[str] = None,
        xrefs: Optional[List[Entity]] = None,
    ) -> None:
        """Build a gene modification variant data dictionary.

        :param name: The name of the gene modification
        :param namespace: The namespace of the gene modification
        :param identifier: The identifier of the name in the database

        Either the name or the identifier must be used. If the namespace is omitted, it is assumed that a name is
        specified from the BEL default namespace.

        Example from BEL default namespace:

        >>> GeneModification(name='Me')

        Example from custom namespace:

        >>> GeneModification(name='DNA methylation', namespace='GO', identifier='GO:0006306',)
        """
        super().__init__(kind=GMOD)

        self[CONCEPT] = Entity(
            namespace=(namespace or BEL_DEFAULT_NAMESPACE),
            name=name,
            identifier=identifier,
        )
        if xrefs:
            self[XREFS] = xrefs

    @property
    def entity(self) -> Entity:
        """Represent the entity in this gene modification."""
        return self[CONCEPT]

    def as_bel(self, use_identifiers: bool = True) -> str:
        """Return this gene modification variant as a BEL string."""
        if use_identifiers and self.entity.identifier and self.entity.name:
            x = self.entity.obo
        else:
            x = self.entity.curie

        return 'gmod({})'.format(x)


class Hgvs(Variant):
    """Builds a HGVS variant dictionary."""

    def __init__(self, variant: str) -> None:
        """Build an HGVS variant data dictionary.

        :param variant: The HGVS variant string

        Example:
        >>> Protein(namespace='HGNC', name='AKT1', variants=[Hgvs('p.Ala127Tyr')])

        """
        super().__init__(kind=HGVS)
        self[HGVS] = variant

    @property
    def variant(self) -> str:  # noqa: D401
        """The HGVS variant string."""
        return self[HGVS]

    def as_bel(self, use_identifiers: bool = True) -> str:
        """Return this HGVS variant as a BEL string."""
        return 'var("{}")'.format(self.variant)


class HgvsReference(Hgvs):
    """Represents the "reference" variant in HGVS."""

    def __init__(self) -> None:
        super().__init__(variant='=')


class HgvsUnspecified(Hgvs):
    """Represents an unspecified variant in HGVS."""

    def __init__(self) -> None:
        super().__init__(variant='?')


class ProteinSubstitution(Hgvs):
    """A protein substitution variant."""

    def __init__(self, from_aa: str, position: int, to_aa: str) -> None:
        """Build an HGVS variant data dictionary for the given protein substitution.

        :param from_aa: The 3-letter amino acid code of the original residue
        :param position: The position of the residue
        :param to_aa: The 3-letter amino acid code of the new residue

        Example:
        >>> Protein(namespace='HGNC', name='AKT1', variants=[ProteinSubstitution('Ala', 127, 'Tyr')])

        """
        super().__init__('p.{}{}{}'.format(from_aa, position, to_aa))


class Fragment(Variant):
    """Represent the information about a protein fragment."""

    def __init__(
        self,
        start: Union[None, int, str] = None,
        stop: Union[None, int, str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Build a protein fragment data dictionary.

        :param start: The starting position
        :param stop: The stopping position
        :param description: An optional description

        Example of specified fragment:

        >>> Protein(name='APP', namespace='HGNC', variants=[Fragment(start=672, stop=713)])

        Example of unspecified fragment:

        >>> Protein(name='APP', namespace='HGNC', variants=[Fragment()])

        """
        super().__init__(kind=FRAGMENT)

        if start and stop:
            self[FRAGMENT_START] = start
            self[FRAGMENT_STOP] = stop
        else:
            self[FRAGMENT_MISSING] = '?'

        if description:
            self[FRAGMENT_DESCRIPTION] = description

    @property
    def range(self) -> str:
        """Get the range of this fragment."""
        if FRAGMENT_MISSING in self:
            return '?'

        return '{}_{}'.format(self[FRAGMENT_START], self[FRAGMENT_STOP])

    def as_bel(self, use_identifiers=False) -> str:
        """Return this fragment variant as a BEL string."""
        res = '"{}"'.format(self.range)

        if FRAGMENT_DESCRIPTION in self:
            res += ', "{}"'.format(self[FRAGMENT_DESCRIPTION])

        return 'frag({})'.format(res)


class Gene(CentralDogma):
    """Builds a gene node."""

    function = GENE

    def get_rna(self) -> 'Rna':
        """Get the corresponding RNA."""
        if self.variants:
            raise InferCentralDogmaException('can not get gene for variant')
        return Rna(
            namespace=self.namespace,
            name=self.name,
            identifier=self.identifier,
            xrefs=self.xrefs,
        )


class _Transcribable(CentralDogma):
    """A base class for RNA and micro-RNA to share getting of their corresponding genes."""

    def get_gene(self) -> Gene:
        """Get the corresponding gene or raise an exception if it's not the reference node.

        :raises: InferCentralDogmaException
        """
        if self.variants:
            raise InferCentralDogmaException('can not get gene for variant')

        return Gene(
            namespace=self.namespace,
            name=self.name,
            identifier=self.identifier,
            xrefs=self.xrefs,
        )


class Rna(_Transcribable):
    """Builds an RNA node.

    Example: AKT1 protein coding gene's RNA:

    >>> Rna(namespace='HGNC', name='AKT1', identifier='391')

    Non-coding RNAs can also be encoded such as `U85 <https://www-snorna.biotoul.fr/plus.php?id=U85>`_:

    >>> Rna(namespace='SNORNABASE', identifier='SR0000073')
    """

    function = RNA


class MicroRna(_Transcribable):
    """Represents an micro-RNA.

    Human miRNA's are listed on HUGO's `MicroRNAs (MIR) <https://www.genenames.org/cgi-bin/genefamilies/set/476>`_
    gene family.

    MIR1-1 from `HGNC <https://www.genenames.org/cgi-bin/gene_symbol_report?hgnc_id=31499>`_:

    >>> MicroRna(namespace='HGNC', name='MIR1-1', identifier='31499')

    MIR1-1 from `miRBase <http://www.mirbase.org/cgi-bin/mirna_entry.pl?acc=MI0000651>`_:

    >>> MicroRna(namespace='MIRBASE', identifier='MI0000651')

    MIR1-1 from `Entrez Gene <https://view.ncbi.nlm.nih.gov/gene/406904>`_

    >>> MicroRna(namespace='ENTREZ', identifier='406904')
    """

    function = MIRNA


class Protein(CentralDogma):
    """Builds a protein node.

    Example: AKT

    >>> Protein(namespace='HGNC', name='AKT1')

    Example: AKT with optionally included HGNC database identifier

    >>> Protein(namespace='HGNC', name='AKT1', identifier='391')

    Example: AKT with phosphorylation

    >>> Protein(namespace='HGNC', name='AKT', variants=[ProteinModification('Ph', code='Thr', position=308)])
    """

    function = PROTEIN

    def get_rna(self) -> Rna:
        """Get the corresponding RNA or raise an exception if it's not the reference node.

        :raises: InferCentralDogmaException
        """
        if self.variants:
            raise InferCentralDogmaException('can not get rna for variant')

        return Rna(
            namespace=self.namespace,
            name=self.name,
            identifier=self.identifier,
            xrefs=self.xrefs,
        )


def _entity_list_as_bel(entities: Iterable[BaseEntity], use_identifiers: bool = True) -> str:
    """Stringify a list of BEL entities."""
    return ', '.join(
        e.as_bel(use_identifiers=use_identifiers)
        for e in entities
    )


class Reaction(BaseEntity):
    """Build a reaction node."""

    function = REACTION

    def __init__(
        self,
        reactants: Union[BaseAbundance, Iterable[BaseAbundance]],
        products: Union[BaseAbundance, Iterable[BaseAbundance]],
    ) -> None:
        """Build a reaction node.

        :param reactants: A list of PyBEL node data dictionaries representing the reactants
        :param products: A list of PyBEL node data dictionaries representing the products

        Example:
        >>> Reaction([Protein(namespace='HGNC', name='KNG1')], [Abundance(namespace='CHEBI', name='bradykinin')])

        """
        super().__init__()

        if isinstance(reactants, BaseEntity):
            reactants = [reactants]
        else:
            reactants = sorted(reactants, key=_as_bel)

        if isinstance(products, BaseEntity):
            products = [products]
        else:
            products = sorted(products, key=_as_bel)

        if not reactants and not products:
            raise ReactionEmptyException('Reaction can not be instantiated with an empty members list.')

        self.update({
            REACTANTS: reactants,
            PRODUCTS: products,
        })

    @property
    def reactants(self) -> List[BaseAbundance]:
        """Return the list of reactants in this reaction."""
        return self[REACTANTS]

    @property
    def products(self) -> List[BaseAbundance]:
        """Return the list of products in this reaction."""
        return self[PRODUCTS]

    def get_catalysts(self) -> Set[BaseAbundance]:
        """Get entities appearing in both the reactants and products."""
        return set(self.reactants).intersection(self.products)

    def as_bel(self, use_identifiers: bool = True) -> str:
        """Return this reaction as a BEL string."""
        return 'rxn(reactants({}), products({}))'.format(
            _entity_list_as_bel(self.reactants, use_identifiers=use_identifiers),
            _entity_list_as_bel(self.products, use_identifiers=use_identifiers),
        )


class ListAbundance(BaseEntity):
    """The superclass for building list abundance (complex, abundance) node data dictionaries."""

    def __init__(self, members: Union[BaseAbundance, Iterable[BaseAbundance]]) -> None:
        """Build a list abundance node.

        :param members: A list of PyBEL node data dictionaries
        """
        super().__init__()

        if isinstance(members, BaseEntity):
            self[MEMBERS] = [members]
        else:
            self[MEMBERS] = sorted(members, key=_as_bel)

        if not self[MEMBERS]:
            raise ListAbundanceEmptyException('List abundance can not be instantiated with an empty members list.')

    @property
    def members(self) -> List[BaseAbundance]:
        """Return the list of members in this list abundance."""
        return self[MEMBERS]

    def as_bel(self, use_identifiers: bool = True) -> str:
        """Return this list abundance as a BEL string."""
        return '{}({})'.format(
            self._bel_function,
            _entity_list_as_bel(self.members, use_identifiers=use_identifiers),
        )


class ComplexAbundance(ListAbundance):
    """Build a complex abundance node with the optional ability to specify a name."""

    function = COMPLEX

    def __init__(
        self,
        members: Iterable[BaseAbundance],
        namespace: Optional[str] = None,
        name: Optional[str] = None,
        identifier: Optional[str] = None,
        xrefs: Optional[List[Entity]] = None,
    ) -> None:
        """Build a complex list node.

        :param members: A list of PyBEL node data dictionaries
        :param namespace: The namespace from which the name originates
        :param name: The name of the complex
        :param identifier: The identifier in the namespace in which the name originates
        :param xrefs: Alternate identifiers for the entity if it is named
        """
        super().__init__(members=members)
        if namespace:
            self[CONCEPT] = Entity(
                namespace=namespace,
                name=name,
                identifier=identifier,
            )
            if xrefs:
                self[XREFS] = xrefs

    @property
    def entity(self) -> Optional[Entity]:  # noqa:D401
        """The concept represented by this complex if it has been named."""
        return self.get(CONCEPT)

    @property
    def xrefs(self) -> List[Entity]:  # noqa:D401
        """Alternative identifiers for the concept if it has been named."""
        return self.get(XREFS, [])


class NamedComplexAbundance(BaseAbundance):
    """Build a named complex abundance node.

    Example:
    >>> NamedComplexAbundance(namespace='FPLX', name='Calcineurin Complex')

    """

    function = COMPLEX


class CompositeAbundance(ListAbundance):
    """Build a composite abundance node."""

    function = COMPOSITE


class FusionRangeBase(dict, metaclass=ABCMeta):
    """The superclass for fusion range data dictionaries."""

    @abstractmethod
    def as_bel(self) -> str:
        """Return this fusion range as BEL."""

    def __str__(self):  # noqa: D105
        return self.as_bel()


class MissingFusionRange(FusionRangeBase):
    """Represents a fusion range with no defined start or end."""

    def __init__(self):
        """Build a missing fusion range."""
        super(MissingFusionRange, self).__init__({
            FUSION_MISSING: '?',
        })

    def as_bel(self) -> str:
        """Return this missing fusion range as BEL."""
        return '?'


class EnumeratedFusionRange(FusionRangeBase):
    """Represents an enumerated fusion range."""

    def __init__(self, reference: str, start, stop):
        """Build an enumerated fusion range.

        :param reference: The reference code
        :param int or str start: The start position, either specified by its integer position, or '?'
        :param int or str stop: The stop position, either specified by its integer position, '?', or '*

        Example fully specified RNA fusion range:

        >>> EnumeratedFusionRange('r', 1, 79)

        """
        super().__init__({
            FUSION_REFERENCE: reference,
            FUSION_START: start,
            FUSION_STOP: stop,
        })

    def as_bel(self) -> str:
        """Return this fusion range as a BEL string."""
        return '{reference}.{start}_{stop}'.format(
            reference=self[FUSION_REFERENCE],
            start=self[FUSION_START],
            stop=self[FUSION_STOP],
        )


class FusionBase(BaseEntity):
    """The superclass for building fusion node data dictionaries."""

    def __init__(
        self,
        partner_5p: CentralDogma,
        partner_3p: CentralDogma,
        range_5p: Optional[FusionRangeBase] = None,
        range_3p: Optional[FusionRangeBase] = None,
    ) -> None:
        """Build a fusion node.

        :param partner_5p: A PyBEL node for the 5-prime partner
        :param partner_3p: A PyBEL node for the 3-prime partner
        :param range_5p: A fusion range for the 5-prime partner
        :param range_3p: A fusion range for the 3-prime partner
        """
        super().__init__()
        self[FUSION] = {
            PARTNER_5P: partner_5p,
            PARTNER_3P: partner_3p,
            RANGE_5P: range_5p or MissingFusionRange(),
            RANGE_3P: range_3p or MissingFusionRange(),
        }

    @property
    def partner_5p(self) -> CentralDogma:
        """Get the 5' partner."""
        return self[FUSION][PARTNER_5P]

    @property
    def partner_3p(self) -> CentralDogma:
        """Get the 3' partner."""
        return self[FUSION][PARTNER_3P]

    @property
    def range_5p(self) -> FusionRangeBase:
        """Get the 5' partner's range."""
        return self[FUSION][RANGE_5P]

    @property
    def range_3p(self) -> FusionRangeBase:
        """Get the 3' partner's range."""
        return self[FUSION][RANGE_3P]

    def as_bel(self, use_identifiers: bool = True) -> str:
        """Return this fusion as a BEL string."""
        if use_identifiers and self.partner_3p.entity.identifier and self.partner_3p.entity.name:
            p3p = self.partner_3p.obo
        else:
            p3p = self.partner_3p.curie

        if use_identifiers and self.partner_5p.entity.identifier and self.partner_5p.entity.name:
            p5p = self.partner_5p.obo
        else:
            p5p = self.partner_5p.curie

        return '{}(fus({}, "{}", {}, "{}"))'.format(
            self._bel_function,
            p5p,
            self.range_5p.as_bel(),
            p3p,
            self.range_3p.as_bel(),
        )


class ProteinFusion(FusionBase):
    """Builds a protein fusion node."""

    function = PROTEIN


class RnaFusion(FusionBase):
    """Builds an RNA fusion node.

    Example, with fusion ranges using the 'r' qualifier:

    >>> RnaFusion(
    >>> ... partner_5p=Rna(namespace='HGNC', name='TMPRSS2'),
    >>> ... range_5p=EnumeratedFusionRange('r', 1, 79),
    >>> ... partner_3p=Rna(namespace='HGNC', name='ERG'),
    >>> ... range_3p=EnumeratedFusionRange('r', 312, 5034)
    >>> )


    Example with missing fusion ranges:

    >>> RnaFusion(
    >>> ... partner_5p=Rna(namespace='HGNC', name='TMPRSS2'),
    >>> ... partner_3p=Rna(namespace='HGNC', name='ERG'),
    >>> )

    """

    function = RNA


class GeneFusion(FusionBase):
    """Builds a gene fusion node.

    Example, using fusion ranges with the 'c' qualifier

    >>> GeneFusion(
    >>> ... partner_5p=Gene(namespace='HGNC', name='TMPRSS2'),
    >>> ... range_5p=EnumeratedFusionRange('c', 1, 79),
    >>> ... partner_3p=Gene(namespace='HGNC', name='ERG'),
    >>> ... range_3p=EnumeratedFusionRange('c', 312, 5034)
    >>> )

    Example with missing fusion ranges:

    >>> GeneFusion(
    >>> ... partner_5p=Gene(namespace='HGNC', name='TMPRSS2'),
    >>> ... partner_3p=Gene(namespace='HGNC', name='ERG'),
    >>> )

    """

    function = GENE
