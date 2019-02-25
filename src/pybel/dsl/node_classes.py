# -*- coding: utf-8 -*-

"""Classes for DSL nodes."""

import hashlib
from abc import ABCMeta, abstractmethod
from operator import methodcaller
from typing import Iterable, List, Optional, Union

from .exc import InferCentralDogmaException, PyBELDSLException
from ..constants import (
    ABUNDANCE, BEL_DEFAULT_NAMESPACE, BIOPROCESS, COMPLEX, COMPOSITE, FRAGMENT, FRAGMENT_DESCRIPTION, FRAGMENT_MISSING,
    FRAGMENT_START, FRAGMENT_STOP, FUNCTION, FUSION, FUSION_MISSING, FUSION_REFERENCE, FUSION_START, FUSION_STOP, GENE,
    GMOD, HGVS, IDENTIFIER, KIND, MEMBERS, MIRNA, NAME, NAMESPACE, PARTNER_3P, PARTNER_5P, PATHOLOGY, PMOD, PMOD_CODE,
    PMOD_ORDER, PMOD_POSITION, PRODUCTS, PROTEIN, RANGE_3P, RANGE_5P, REACTANTS, REACTION, RNA, VARIANTS,
    rev_abundance_labels,
)
from ..language import Entity
from ..utils import ensure_quotes

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
    'BaseEntity',
    'BaseAbundance',
    'CentralDogma',
    'ListAbundance',
    'Variant',
    'FusionBase',
    'FusionRangeBase',
]

_as_bel = methodcaller('as_bel')


class BaseEntity(dict, metaclass=ABCMeta):
    """This class represents all BEL nodes. It can be converted to a tuple and hashed."""

    def __init__(self, func: str) -> None:
        """Build a PyBEL node.

        :param func: The PyBEL function
        """
        super().__init__(**{FUNCTION: func})

    @property
    def function(self) -> str:
        """Return the function of this entity."""
        return self[FUNCTION]

    @property
    def _func(self) -> str:
        return rev_abundance_labels[self.function]

    @abstractmethod
    def as_bel(self) -> str:
        """Return this entity as a BEL string."""

    def as_sha512(self) -> str:
        """Return this entity as a SHA512 hash encoded in UTF-8."""
        return hashlib.sha512(self.as_bel().encode('utf8')).hexdigest()

    @property
    def sha512(self) -> str:
        """Get the SHA512 hash of this node."""
        return self.as_sha512()

    def __hash__(self):  # noqa: D105
        return hash(self.as_bel())

    def __eq__(self, other):
        return isinstance(other, BaseEntity) and self.as_bel() == other.as_bel()

    def __repr__(self):
        return '<BEL {bel}>'.format(bel=self.as_bel())

    def __str__(self):  # noqa: D105
        return self.as_bel()


class BaseAbundance(BaseEntity):
    """The superclass for building node data dictionaries."""

    def __init__(self, func: str, namespace: str, name: Optional[str] = None, identifier: Optional[str] = None) -> None:
        """Build an abundance from a function, namespace, and a name and/or identifier.

        :param func: The PyBEL function
        :param namespace: The name of the namespace
        :param name: The name of this abundance
        :param identifier: The database identifier for this abundance
        """
        if name is None and identifier is None:
            raise PyBELDSLException('Either name or identifier must be specified')

        super(BaseAbundance, self).__init__(func=func)
        self.update(Entity(namespace=namespace, name=name, identifier=identifier))

    @property
    def namespace(self) -> str:  # noqa:D401
        """The namespace of this abundance."""
        return self[NAMESPACE]

    @property
    def name(self) -> Optional[str]:  # noqa:D401
        """The name of this abundance."""
        return self.get(NAME)

    @property
    def identifier(self) -> Optional[str]:  # noqa:D401
        """The identifier of this abundance."""
        return self.get(IDENTIFIER)

    @property
    def _priority_id(self):
        return self.name or self.identifier

    def as_bel(self) -> str:
        """Return this node as a BEL string."""
        return "{}({}:{})".format(
            self._func,
            self.namespace,
            ensure_quotes(self._priority_id)
        )


class Abundance(BaseAbundance):
    """Builds an abundance node."""

    def __init__(self, namespace: str, name: Optional[str] = None, identifier: Optional[str] = None) -> None:
        """Build a general abundance entity.

        :param namespace: The name of the database used to identify this entity
        :param name: The database's preferred name or label for this entity
        :param identifier: The database's identifier for this entity

        Example:

        >>> Abundance(namespace='CHEBI', name='water')
        """
        super(Abundance, self).__init__(ABUNDANCE, namespace=namespace, name=name, identifier=identifier)


class BiologicalProcess(BaseAbundance):
    """Builds a biological process node."""

    def __init__(self, namespace: str, name: Optional[str] = None, identifier: Optional[str] = None) -> None:
        """Build a biological process node.

        :param namespace: The name of the database used to identify this biological process
        :param name: The database's preferred name or label for this biological process
        :param identifier: The database's identifier for this biological process

        Example:

        >>> BiologicalProcess(namespace='GO', name='apoptosis')
        """
        super(BiologicalProcess, self).__init__(BIOPROCESS, namespace=namespace, name=name, identifier=identifier)


class Pathology(BaseAbundance):
    """Builds a pathology node."""

    def __init__(self, namespace: str, name: Optional[str] = None, identifier: Optional[str] = None) -> None:
        """Build a pathology node.

        :param namespace: The name of the database used to identify this pathology
        :param name: The database's preferred name or label for this pathology
        :param identifier: The database's identifier for this pathology

        Example:

        >>> Pathology(namespace='DO', name='Alzheimer Disease')
        """
        super(Pathology, self).__init__(PATHOLOGY, namespace=namespace, name=name, identifier=identifier)


class CentralDogma(BaseAbundance):
    """The base class for "central dogma" abundances (i.e., genes, miRNAs, RNAs, and proteins)."""

    def __init__(self,
                 func: str,
                 namespace: str,
                 name: Optional[str] = None,
                 identifier: Optional[str] = None,
                 variants: Union[None, 'Variant', Iterable['Variant']] = None,
                 ) -> None:
        """Build a node for a gene, RNA, miRNA, or protein.

        :param func: The PyBEL function to use
        :param namespace: The name of the database used to identify this entity
        :param name: The database's preferred name or label for this entity
        :param identifier: The database's identifier for this entity
        :param variants: An optional variant or list of variants
        """
        super(CentralDogma, self).__init__(func, namespace, name=name, identifier=identifier)
        if variants:
            self[VARIANTS] = (
                [variants]
                if isinstance(variants, Variant) else
                sorted(variants, key=_as_bel)
            )

    @property
    def variants(self) -> Optional[List['Variant']]:
        """Return this entity's variants, if they exist."""
        return self.get(VARIANTS)

    def as_bel(self) -> str:
        """Return this node as a BEL string."""
        variants = self.get(VARIANTS)

        if not variants:
            return super(CentralDogma, self).as_bel()

        variants_canon = sorted(map(str, variants))

        return "{}({}:{}, {})".format(
            self._func,
            self.namespace,
            ensure_quotes(self._priority_id),
            ', '.join(variants_canon)
        )

    def get_parent(self) -> Optional['CentralDogma']:
        """Get the parent, or none if it's already a reference node.

        :rtype: Optional[CentralDogma]

        Example usage:

        >>> ab42 = Protein(name='APP', namespace='HGNC', variants=[Fragment(start=672, stop=713)])
        >>> app = ab42.get_parent()
        >>> assert 'p(HGNC:APP)' == app.as_bel()
        """
        if VARIANTS not in self:
            return

        return self.__class__(namespace=self.namespace, name=self.name, identifier=self.identifier)

    def with_variants(self, variants: Union['Variant', List['Variant']]) -> 'CentralDogma':
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
            variants=variants,
        )


class Variant(dict, metaclass=ABCMeta):
    """The superclass for variant dictionaries."""

    def __init__(self, kind: str) -> None:
        """Build the variant data dictionary.

        :param kind: The kind of variant
        """
        super(Variant, self).__init__({KIND: kind})

    @abstractmethod
    def as_bel(self) -> str:
        """Return this variant as a BEL string."""

    def __str__(self):  # noqa: D105
        return self.as_bel()


class ProteinModification(Variant):
    """Build a protein modification variant dictionary."""

    def __init__(self,
                 name: str,
                 code: Optional[str] = None,
                 position: Optional[int] = None,
                 namespace: Optional[str] = None,
                 identifier: Optional[str] = None,
                 ) -> None:
        """Build a protein modification variant data dictionary.

        :param name: The name of the modification
        :param code: The three letter amino acid code for the affected residue. Capital first letter.
        :param position: The position of the affected residue
        :param namespace: The namespace to which the name of this modification belongs
        :param identifier: The identifier of the name of the modification

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
        super(ProteinModification, self).__init__(PMOD)

        self[IDENTIFIER] = Entity(
            namespace=(namespace or BEL_DEFAULT_NAMESPACE),
            name=name,
            identifier=identifier
        )

        if code:
            self[PMOD_CODE] = code

        if position:
            self[PMOD_POSITION] = position

    def as_bel(self) -> str:
        """Return this protein modification variant as a BEL string."""
        return 'pmod({}{})'.format(
            str(self[IDENTIFIER]),
            ''.join(', {}'.format(self[x]) for x in PMOD_ORDER[2:] if x in self)
        )


class GeneModification(Variant):
    """Build a gene modification variant dictionary."""

    def __init__(self, name, namespace=None, identifier=None):
        """Build a gene modification variant data dictionary.

        :param str name: The name of the gene modification
        :param Optional[str] namespace: The namespace of the gene modification
        :param Optional[str] identifier: The identifier of the name in the database

        Either the name or the identifier must be used. If the namespace is omitted, it is assumed that a name is
        specified from the BEL default namespace.

        Example from BEL default namespace:

        >>> GeneModification(name='Me')

        Example from custom namespace:

        >>> GeneModification(name='DNA methylation', namespace='GO', identifier='GO:0006306',)
        """
        super(GeneModification, self).__init__(GMOD)

        self[IDENTIFIER] = Entity(
            namespace=(namespace or BEL_DEFAULT_NAMESPACE),
            name=name,
            identifier=identifier
        )

    def as_bel(self) -> str:
        """Return this gene modification variant as a BEL string."""
        return 'gmod({})'.format(str(self[IDENTIFIER]))


class Hgvs(Variant):
    """Builds a HGVS variant dictionary."""

    def __init__(self, variant: str) -> None:
        """Build an HGVS variant data dictionary.

        :param variant: The HGVS variant string

        Example:

        >>> Protein(namespace='HGNC', name='AKT1', variants=[Hgvs('p.Ala127Tyr')])
        """
        super(Hgvs, self).__init__(HGVS)

        self[IDENTIFIER] = variant

    def as_bel(self) -> str:
        """Return this HGVS variant as a BEL string."""
        return 'var("{}")'.format(self[IDENTIFIER])


class HgvsReference(Hgvs):
    """Represents the "reference" variant in HGVS."""

    def __init__(self) -> None:
        super(HgvsReference, self).__init__('=')


class HgvsUnspecified(Hgvs):
    """Represents an unspecified variant in HGVS."""

    def __init__(self) -> None:
        super(HgvsUnspecified, self).__init__('?')


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
        super(ProteinSubstitution, self).__init__('p.{}{}{}'.format(from_aa, position, to_aa))


class Fragment(Variant):
    """Represent the information about a protein fragment."""

    def __init__(self, start=None, stop=None, description=None):
        """Build a protein fragment data dictionary.

        :param start: The starting position
        :type start: None or int or str
        :param stop: The stopping position
        :type stop: None or int or str
        :param Optional[str] description: An optional description

        Example of specified fragment:

        >>> Protein(name='APP', namespace='HGNC', variants=[Fragment(start=672, stop=713)])

        Example of unspecified fragment:

        >>> Protein(name='APP', namespace='HGNC', variants=[Fragment()])
        """
        super(Fragment, self).__init__(FRAGMENT)

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

    def as_bel(self) -> str:
        """Return this fragment variant as a BEL string."""
        res = '"{}"'.format(self.range)

        if FRAGMENT_DESCRIPTION in self:
            res += ', "{}"'.format(self[FRAGMENT_DESCRIPTION])

        return 'frag({})'.format(res)


class Gene(CentralDogma):
    """Represents a gene."""

    def __init__(self, namespace, name=None, identifier=None, variants=None):
        """Build a gene node.

        :param str namespace: The name of the database used to identify this entity
        :param Optional[str] name: The database's preferred name or label for this entity
        :param Optional[str] identifier: The database's identifier for this entity
        :param variants: An optional variant or list of variants
        :type variants: None or Variant or list[Variant]
        """
        super(Gene, self).__init__(GENE, namespace, name=name, identifier=identifier, variants=variants)


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
            identifier=self.identifier
        )


class Rna(_Transcribable):
    """Represents an RNA."""

    def __init__(self, namespace, name=None, identifier=None, variants=None):
        """Build an RNA node.

        :param str namespace: The name of the database used to identify this entity
        :param Optional[str] name: The database's preferred name or label for this entity
        :param Optional[str] identifier: The database's identifier for this entity
        :param variants: An optional variant or list of variants
        :type variants: None or Variant or list[Variant]

        Example: AKT1 protein coding gene's RNA:

        >>> Rna(namespace='HGNC', name='AKT1', identifier='391')

        Non-coding RNA's can also be encoded such as `U85 <https://www-snorna.biotoul.fr/plus.php?id=U85>`_:

        >>> Rna(namespace='SNORNABASE', identifer='SR0000073')
        """
        super(Rna, self).__init__(RNA, namespace, name=name, identifier=identifier, variants=variants)


class MicroRna(_Transcribable):
    """Represents an micro-RNA."""

    def __init__(self, namespace, name=None, identifier=None, variants=None):
        """Build an miRNA node.

        :param str namespace: The name of the database used to identify this entity
        :param Optional[str] name: The database's preferred name or label for this entity
        :param Optional[str] identifier: The database's identifier for this entity
        :param variants: A list of variants
        :type variants: None or Variant or list[Variant]

        Human miRNA's are listed on HUGO's `MicroRNAs (MIR) <https://www.genenames.org/cgi-bin/genefamilies/set/476>`_
        gene family.

        MIR1-1 from `HGNC <https://www.genenames.org/cgi-bin/gene_symbol_report?hgnc_id=31499>`_:

        >>> MicroRna(namespace='HGNC', name='MIR1-1', identifier='31499')

        MIR1-1 from `miRBase <http://www.mirbase.org/cgi-bin/mirna_entry.pl?acc=MI0000651>`_:

        >>> MicroRna(namespace='MIRBASE', identifier='MI0000651')

        MIR1-1 from `Entrez Gene <https://view.ncbi.nlm.nih.gov/gene/406904>`_

        >>> MicroRna(namespace='ENTREZ', identifier='406904')
        """
        super(MicroRna, self).__init__(MIRNA, namespace, name=name, identifier=identifier, variants=variants)


class Protein(CentralDogma):
    """Represents a protein."""

    def __init__(self, namespace, name=None, identifier=None, variants=None):
        """Build a protein node.

        :param str namespace: The name of the database used to identify this entity
        :param Optional[str] name: The database's preferred name or label for this entity
        :param Optional[str] identifier: The database's identifier for this entity
        :param variants: An optional variant or list of variants
        :type variants: None or Variant or list[Variant]

        Example: AKT

        >>> Protein(namespace='HGNC', name='AKT1')

        Example: AKT with optionally included HGNC database identifier

        >>> Protein(namespace='HGNC', name='AKT1', identifier='391')

        Example: AKT with phosphorylation

        >>> Protein(namespace='HGNC', name='AKT', variants=[ProteinModification('Ph', code='Thr', position=308)])
        """
        super(Protein, self).__init__(PROTEIN, namespace, name=name, identifier=identifier, variants=variants)

    def get_rna(self) -> Rna:
        """Get the corresponding RNA or raise an exception if it's not the reference node.

        :raises: InferCentralDogmaException
        """
        if self.variants:
            raise InferCentralDogmaException('can not get rna for variant')

        return Rna(
            namespace=self.namespace,
            name=self.name,
            identifier=self.identifier
        )


def _entity_list_as_bel(entities: Iterable[BaseEntity]) -> str:
    """Stringify a list of BEL entities."""
    return ', '.join(
        e.as_bel()
        for e in entities
    )


class Reaction(BaseEntity):
    """Build a reaction node."""

    def __init__(self, reactants, products):
        """Build a reaction node.

        :param reactants: A list of PyBEL node data dictionaries representing the reactants
        :type reactants: BaseAbundance or iter[BaseAbundance]
        :param products: A list of PyBEL node data dictionaries representing the products
        :type products: BaseAbundance or iter[BaseAbundance]

        Example:

        >>> reaction([Protein(namespace='HGNC', name='KNG1')], [Abundance(namespace='CHEBI', name='bradykinin')])
        """
        super(Reaction, self).__init__(func=REACTION)

        if isinstance(reactants, BaseEntity):
            reactants = [reactants]
        else:
            reactants = sorted(reactants, key=_as_bel)

        if isinstance(products, BaseEntity):
            products = [products]
        else:
            products = sorted(products, key=_as_bel)

        self.update({
            REACTANTS: reactants,
            PRODUCTS: products,
        })

    @property
    def reactants(self):
        """Return the list of reactants in this reaction.

        :rtype: list[BaseAbundance]
        """
        return self[REACTANTS]

    @property
    def products(self):
        """Return the list of products in this reaction.

        :rtype: list[BaseAbundance]
        """
        return self[PRODUCTS]

    def as_bel(self):
        """Return this reaction as a BEL string.

        :rtype: str
        """
        return 'rxn(reactants({}), products({}))'.format(
            _entity_list_as_bel(self.reactants),
            _entity_list_as_bel(self.products)
        )


reaction = Reaction


class ListAbundance(BaseEntity):
    """The superclass for building list abundance (complex, abundance) node data dictionaries."""

    def __init__(self, func, members):
        """Build a list abundance node.

        :param str func: The PyBEL function
        :param members: A list of PyBEL node data dictionaries
        :type members: BaseAbundance or list[BaseAbundance]
        """
        super(ListAbundance, self).__init__(func=func)

        if isinstance(members, BaseEntity):
            self[MEMBERS] = [members]
        elif 0 == len(members):
            raise ValueError('List abundance can not be instantiated with an empty members list.')
        else:
            self[MEMBERS] = sorted(members, key=_as_bel)

    @property
    def members(self):
        """Return the list of members in this list abundance.

        :rtype: list[BaseAbundance]
        """
        return self[MEMBERS]

    def as_bel(self):
        """Return this list abundance as a BEL string.

        :rtype: str
        """
        return '{}({})'.format(
            self._func,
            _entity_list_as_bel(self.members)
        )


class ComplexAbundance(ListAbundance):
    """Build a complex abundance node with the optional ability to specify a name."""

    def __init__(self, members, namespace=None, name=None, identifier=None):
        """Build a complex list node.

        :param list[BaseAbundance] members: A list of PyBEL node data dictionaries
        :param Optional[str] namespace: The namespace from which the name originates
        :param Optional[str] name: The name of the complex
        :param Optional[str] identifier: The identifier in the namespace in which the name originates
        """
        super(ComplexAbundance, self).__init__(func=COMPLEX, members=members)

        if namespace:
            self.update(Entity(namespace=namespace, name=name, identifier=identifier))


class NamedComplexAbundance(BaseAbundance):
    """Build a named complex abundance node."""

    def __init__(self, namespace=None, name=None, identifier=None):
        """Build a complex abundance node.

        :param str namespace: The name of the database used to identify this entity
        :param str name: The database's preferred name or label for this entity
        :param str identifier: The database's identifier for this entity

        Example:

        >>> NamedComplexAbundance(namespace='SCOMP', name='Calcineurin Complex')
        """
        super(NamedComplexAbundance, self).__init__(
            func=COMPLEX,
            namespace=namespace,
            name=name,
            identifier=identifier,
        )


class CompositeAbundance(ListAbundance):
    """Build a composite abundance node."""

    def __init__(self, members):
        """Build a composite abundance node.

        :param list[BaseAbundance] members: A list of PyBEL node data dictionaries
        """
        super(CompositeAbundance, self).__init__(func=COMPOSITE, members=members)


class FusionRangeBase(dict, metaclass=ABCMeta):
    """The superclass for fusion range data dictionaries."""

    @abstractmethod
    def as_bel(self):
        """Return this fusion range as BEL.

        :rtype: str
        """

    def __str__(self):  # noqa: D105
        return self.as_bel()


class MissingFusionRange(FusionRangeBase):
    """Represents a fusion range with no defined start or end."""

    def __init__(self):
        """Build a missing fusion range."""
        super(MissingFusionRange, self).__init__({
            FUSION_MISSING: '?'
        })

    def as_bel(self) -> str:
        """Return this missing fusion range as BEL."""
        return '?'


class EnumeratedFusionRange(FusionRangeBase):
    """Represents an enumerated fusion range."""

    def __init__(self, reference, start, stop):
        """Build an enumerated fusion range.

        :param str reference: The reference code
        :param int or str start: The start position, either specified by its integer position, or '?'
        :param int or str stop: The stop position, either specified by its integer position, '?', or '*

        Example fully specified RNA fusion range:

        >>> EnumeratedFusionRange('r', 1, 79)

        """
        super(EnumeratedFusionRange, self).__init__({
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

    def __init__(self,
                 func,
                 partner_5p: CentralDogma,
                 partner_3p: CentralDogma,
                 range_5p: Optional[FusionRangeBase] = None,
                 range_3p: Optional[FusionRangeBase] = None,
                 ) -> None:
        """Build a fusion node.

        :param func: A PyBEL function
        :param partner_5p: A PyBEL node for the 5-prime partner
        :param partner_3p: A PyBEL node for the 3-prime partner
        :param range_5p: A fusion range for the 5-prime partner
        :param ange_3p: A fusion range for the 3-prime partner
        """
        super(FusionBase, self).__init__(func=func)
        self[FUSION] = {
            PARTNER_5P: partner_5p,
            PARTNER_3P: partner_3p,
            RANGE_5P: range_5p or MissingFusionRange(),
            RANGE_3P: range_3p or MissingFusionRange()
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

    def as_bel(self) -> str:
        """Return this fusion as a BEL string."""
        return '{}(fus({}:{}, "{}", {}:{}, "{}"))'.format(
            self._func,
            self.partner_5p.namespace,
            self.partner_5p._priority_id,
            self.range_5p.as_bel(),
            self.partner_3p.namespace,
            self.partner_3p._priority_id,
            self.range_3p.as_bel(),
        )


class ProteinFusion(FusionBase):
    """Builds a protein fusion data dictionary."""

    def __init__(self,
                 partner_5p: Protein,
                 partner_3p: Protein,
                 range_5p: Optional[FusionRangeBase] = None,
                 range_3p: Optional[FusionRangeBase] = None,
                 ) -> None:
        """Build a protein fusion node.

        :param partner_5p: A PyBEL node for the 5-prime partner
        :param partner_3p: A PyBEL node for the 3-prime partner
        :param range_5p: A fusion range for the 5-prime partner
        :param range_3p: A fusion range for the 3-prime partner
        """
        super(ProteinFusion, self).__init__(
            func=PROTEIN,
            partner_5p=partner_5p,
            range_5p=range_5p,
            partner_3p=partner_3p,
            range_3p=range_3p,
        )


class RnaFusion(FusionBase):
    """Builds an RNA fusion data dictionary."""

    def __init__(self,
                 partner_5p: Rna,
                 partner_3p: Rna,
                 range_5p: Optional[FusionRangeBase] = None,
                 range_3p: Optional[FusionRangeBase] = None,
                 ) -> None:
        """Build an RNA fusion node.

        :param partner_5p: A PyBEL node for the 5-prime partner
        :param partner_3p: A PyBEL node for the 3-prime partner
        :param range_5p: A fusion range for the 5-prime partner
        :param range_3p: A fusion range for the 3-prime partner

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
        super(RnaFusion, self).__init__(
            func=RNA,
            partner_5p=partner_5p,
            range_5p=range_5p,
            partner_3p=partner_3p,
            range_3p=range_3p,
        )


class GeneFusion(FusionBase):
    """Builds a gene fusion data dictionary."""

    def __init__(self,
                 partner_5p: Gene,
                 partner_3p: Gene,
                 range_5p: Optional[FusionRangeBase] = None,
                 range_3p: Optional[FusionRangeBase] = None,
                 ) -> None:
        """Build a gene fusion node.

        :param partner_5p: A PyBEL node for the 5-prime partner
        :param partner_3p: A PyBEL node for the 3-prime partner
        :param range_5p: A fusion range for the 5-prime partner
        :param range_3p: A fusion range for the 3-prime partner

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
        super(GeneFusion, self).__init__(
            func=GENE,
            partner_5p=partner_5p,
            range_5p=range_5p,
            partner_3p=partner_3p,
            range_3p=range_3p,
        )
