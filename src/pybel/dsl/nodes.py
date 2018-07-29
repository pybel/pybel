# -*- coding: utf-8 -*-

"""Internal DSL functions for nodes."""

import abc

import six

from .exc import InferCentralDogmaException, PyBELDSLException
from .utils import entity
from ..constants import (
    ABUNDANCE, BEL_DEFAULT_NAMESPACE, BIOPROCESS, COMPLEX, COMPOSITE, FRAGMENT, FRAGMENT_DESCRIPTION, FRAGMENT_MISSING,
    FRAGMENT_START, FRAGMENT_STOP, FUNCTION, FUSION, FUSION_MISSING, FUSION_REFERENCE, FUSION_START, FUSION_STOP, GENE,
    GMOD, GMOD_ORDER, HGVS, IDENTIFIER, KIND, MEMBERS, MIRNA, NAME, NAMESPACE, PARTNER_3P, PARTNER_5P, PATHOLOGY, PMOD,
    PMOD_CODE, PMOD_ORDER, PMOD_POSITION, PRODUCTS, PROTEIN, RANGE_3P, RANGE_5P, REACTANTS, REACTION, RNA, VARIANTS,
    rev_abundance_labels,
)
from ..utils import ensure_quotes, hash_node

__all__ = [
    'abundance',
    'gene',
    'rna',
    'mirna',
    'protein',
    'complex_abundance',
    'composite_abundance',
    'bioprocess',
    'pathology',
    'named_complex_abundance',
    'reaction',
    'pmod',
    'gmod',
    'hgvs',
    'protein_substitution',
    'fragment',
    'fusion_range',
    'missing_fusion_range',
    'protein_fusion',
    'rna_fusion',
    'gene_fusion',
]


@six.add_metaclass(abc.ABCMeta)
class BaseEntity(dict):
    """This class represents all BEL nodes. It can be converted to a tuple and hashed."""

    def __init__(self, func):
        """
        :param str func: The PyBEL function
        """
        super(BaseEntity, self).__init__(**{FUNCTION: func})

    @abc.abstractmethod
    def as_tuple(self):
        """Return this entity as a PyBEL tuple.

        :rtype: tuple
        """

    @abc.abstractmethod
    def as_bel(self):
        """Return this entity as a BEL string.

        :rtype: tuple
        """

    def as_sha512(self):
        """Return this entity as a SHA512 hash encoded in UTF-8.

        :rtype: str
        """
        return hash_node(self.as_tuple())

    def __hash__(self):
        return hash(self.as_tuple())

    def __str__(self):
        return self.as_bel()


class BaseAbundance(BaseEntity):
    """The superclass for building node data dictionaries."""

    def __init__(self, func, namespace, name=None, identifier=None):
        """Build an abundance from a function, namespace, and a name and/or identifier.

        :param str func: The PyBEL function
        :param str namespace: The name of the namespace
        :param Optional[str] name: The name of this abundance
        :param Optional[str] identifier: The database identifier for this abundance
        """
        if name is None and identifier is None:
            raise PyBELDSLException('Either name or identifier must be specified')

        super(BaseAbundance, self).__init__(func=func)
        self.update(entity(namespace=namespace, name=name, identifier=identifier))

    @property
    def function(self):
        """Return the function of this abundance.

        :rtype: str
        """
        return self[FUNCTION]

    @property
    def namespace(self):
        """Return the namespace of this abundance.

        :rtype: str
        """
        return self[NAMESPACE]

    @property
    def name(self):
        """Return the name of this abundance.

        :rtype: Optional[str]
        """
        return self.get(NAME)

    @property
    def identifier(self):
        """Return the identifier of this abundance.

        :rtype: Optional[str]
        """
        return self.get(IDENTIFIER)

    @property
    def _priority_id(self):
        return self.name or self.identifier

    def as_tuple(self):
        """Return this node as a PyBEL node tuple.

        :rtype: tuple
        """
        return self.function, self.namespace, self._priority_id

    def as_bel(self):
        """Return this node as a BEL string.

        :rtype: str
        """
        return "{}({}:{})".format(
            rev_abundance_labels[self.function],
            self[NAMESPACE],
            ensure_quotes(self._priority_id)
        )


class Abundance(BaseAbundance):
    """Builds an abundance node data dictionary."""

    def __init__(self, namespace, name=None, identifier=None):
        """Build a general abundance entity.

        :param str namespace: The name of the database used to identify this entity
        :param Optional[str] name: The database's preferred name or label for this entity
        :param Optional[str] identifier: The database's identifier for this entity

        Example:

        >>> abundance(namespace='CHEBI', name='water')
        """
        super(Abundance, self).__init__(ABUNDANCE, namespace=namespace, name=name, identifier=identifier)


abundance = Abundance


class BiologicalProcess(BaseAbundance):
    """Builds a biological process node data dictionary."""

    def __init__(self, namespace, name=None, identifier=None):
        """Build a biological process node data dictionary.

        :param str namespace: The name of the database used to identify this biological process
        :param Optional[str] name: The database's preferred name or label for this biological process
        :param Optional[str] identifier: The database's identifier for this biological process

        Example:

        >>> bioprocess(namespace='GO', name='apoptosis')
        """
        super(BiologicalProcess, self).__init__(BIOPROCESS, namespace=namespace, name=name, identifier=identifier)


bioprocess = BiologicalProcess


class Pathology(BaseAbundance):
    """Builds a pathology node data dictionary."""

    def __init__(self, namespace, name=None, identifier=None):
        """Build a pathology node data dictionary.

        :param str namespace: The name of the database used to identify this pathology
        :param Optional[str] name: The database's preferred name or label for this pathology
        :param Optional[str] identifier: The database's identifier for this pathology

        Example:

        >>> pathology(namespace='DO', name='Alzheimer Disease')
        """
        super(Pathology, self).__init__(PATHOLOGY, namespace=namespace, name=name, identifier=identifier)


pathology = Pathology


class CentralDogma(BaseAbundance):
    """Builds a central dogma (gene, mirna, rna, protein) node data dictionary"""

    def __init__(self, func, namespace, name=None, identifier=None, variants=None):
        """Build a node data dictionary for a gene, RNA, miRNA, or protein.

        :param str func: The PyBEL function to use
        :param str namespace: The name of the database used to identify this entity
        :param Optional[str] name: The database's preferred name or label for this entity
        :param Optional[str] identifier: The database's identifier for this entity
        :param variants: An optional variant or list of variants
        :type variants: None or Variant or list[Variant]
        """
        super(CentralDogma, self).__init__(func, namespace, name=name, identifier=identifier)
        if variants:
            self[VARIANTS] = [variants] if isinstance(variants, Variant) else variants

    @property
    def variants(self):
        """Return this entity's variants, if they exist.

        :rtype: Optional[list[Variant]]
        """
        return self.get(VARIANTS)

    def as_tuple(self):
        """Return this node as a PyBEL node tuple.

        :rtype: tuple
        """
        t = super(CentralDogma, self).as_tuple()

        if self.variants:
            return t + _tuplable_list_as_tuple(self.variants)

        return t

    def as_bel(self):
        """Return this node as a BEL string.

        :rtype: str
        """
        variants = self.get(VARIANTS)

        if not variants:
            return super(CentralDogma, self).as_bel()

        variants_canon = sorted(map(str, variants))

        return "{}({}:{}, {})".format(
            rev_abundance_labels[self[FUNCTION]],
            self[NAMESPACE],
            ensure_quotes(self[NAME]),
            ', '.join(variants_canon)
        )

    def get_parent(self):
        """Get the parent, or none if it's already a reference node.

        :rtype: Optional[CentralDogma]

        Example usage:

        >>> ab42 = protein(name='APP', namespace='HGNC', variants=[fragment(start=672, stop=713)])
        >>> app = ab42.get_parent()
        >>> assert 'p(HGNC:APP)' == app.as_bel()
        """
        if VARIANTS not in self:
            return

        return self.__class__(namespace=self.namespace, name=self.name, identifier=self.identifier)

    def with_variants(self, variants):
        """Create a new entity with the given variants.

        :param Variant or list[Variant] variants: An optional variant or list of variants
        :rtype: CentralDogma

        Example Usage:

        >>> app = protein(name='APP', namespace='HGNC')
        >>> ab42 = app.with_variants([fragment(start=672, stop=713)])
        >>> assert 'p(HGNC:APP, frag(672_713))' == ab42.as_bel()
        """
        return self.__class__(
            namespace=self.namespace,
            name=self.name,
            identifier=self.identifier,
            variants=variants,
        )


@six.add_metaclass(abc.ABCMeta)
class Variant(dict):
    """The superclass for variant dictionaries."""

    def __init__(self, kind):
        """Build the variant data dictionary.

        :param str kind: The kind of variant
        """
        super(Variant, self).__init__({KIND: kind})

    @abc.abstractmethod
    def as_tuple(self):
        """Return this node as a tuple.

        :rtype: tuple
        """

    @abc.abstractmethod
    def as_bel(self):
        """Return this variant as a BEL string.

        :rtype: str
        """

    def __str__(self):
        return self.as_bel()


class ProteinModification(Variant):
    """Build a protein modification variant dictionary."""

    def __init__(self, name, code=None, position=None, namespace=None, identifier=None):
        """Build a protein modification variant data dictionary.

        :param str name: The name of the modification
        :param str code: The three letter amino acid code for the affected residue. Capital first letter.
        :param int position: The position of the affected residue
        :param str namespace: The namespace to which the name of this modification belongs
        :param str identifier: The identifier of the name of the modification

        Either the name or the identifier must be used. If the namespace is omitted, it is assumed that a name is
        specified from the BEL default namespace.

        Example from BEL default namespace:

        >>> pmod('Ph', code='Thr', position=308)

        Example from custom namespace:

        >>> pmod(name='protein phosphorylation', namespace='GO', code='Thr', position=308)

        Example from custom namespace additionally qualified with identifier:

        >>> pmod(name='protein phosphorylation', namespace='GO', identifier='GO:0006468', code='Thr', position=308)
        """
        super(ProteinModification, self).__init__(PMOD)

        self[IDENTIFIER] = entity(
            namespace=(namespace or BEL_DEFAULT_NAMESPACE),
            name=name,
            identifier=identifier
        )

        if code:
            self[PMOD_CODE] = code

        if position:
            self[PMOD_POSITION] = position

    def as_tuple(self):
        """Return this protein modification variant as a tuple.

        :rtype: tuple
        """
        identifier = self[IDENTIFIER][NAMESPACE], self[IDENTIFIER][NAME]
        params = tuple(self[key] for key in PMOD_ORDER[2:] if key in self)
        return (PMOD,) + (identifier,) + params

    def as_bel(self):
        """Return this protein modification variant as a BEL string.

        :rtype: str
        """
        return 'pmod({}{})'.format(
            str(self[IDENTIFIER]),
            ''.join(', {}'.format(self[x]) for x in PMOD_ORDER[2:] if x in self)
        )


pmod = ProteinModification


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

        >>> gmod(name='Me')

        Example from custom namespace:

        >>> gmod(name='DNA methylation', namespace='GO', identifier='GO:0006306',)
        """
        super(GeneModification, self).__init__(GMOD)

        self[IDENTIFIER] = entity(
            namespace=(namespace or BEL_DEFAULT_NAMESPACE),
            name=name,
            identifier=identifier
        )

    def as_tuple(self):
        """Return this gene modification variant as a tuple.

        :rtype: tuple
        """
        identifier = self[IDENTIFIER][NAMESPACE], self[IDENTIFIER][NAME]
        params = tuple(self[key] for key in GMOD_ORDER[2:] if key in self)
        return (GMOD,) + (identifier,) + params

    def as_bel(self):
        """Return this gene modification variant as a BEL string.

        :rtype: str
        """
        return 'gmod({})'.format(str(self[IDENTIFIER]))


gmod = GeneModification


class Hgvs(Variant):
    """Builds a HGVS variant dictionary."""

    def __init__(self, variant):
        """Build an HGVS variant data dictionary.

        :param str variant: The HGVS variant string

        Example:

        >>> protein(namespace='HGNC', name='AKT1', variants=[hgvs('p.Ala127Tyr')])
        """
        super(Hgvs, self).__init__(HGVS)

        self[IDENTIFIER] = variant

    def as_tuple(self):
        """Return this HGVS variant as a tuple.

        :rtype: tuple
        """
        return self[KIND], self[IDENTIFIER]

    def as_bel(self):
        """Return this HGVS variant as a BEL string.

        :rtype: str
        """
        return 'var({})'.format(self[IDENTIFIER])


hgvs = Hgvs


class ProteinSubstitution(Hgvs):
    """A protein substitution variant."""

    def __init__(self, from_aa, position, to_aa):
        """Build an HGVS variant data dictionary for the given protein substitution.

        :param str from_aa: The 3-letter amino acid code of the original residue
        :param int position: The position of the residue
        :param str to_aa: The 3-letter amino acid code of the new residue

        Example:

        >>> protein(namespace='HGNC', name='AKT1', variants=[protein_substitution('Ala', 127, 'Tyr')])
        """
        super(ProteinSubstitution, self).__init__('p.{}{}{}'.format(from_aa, position, to_aa))


protein_substitution = ProteinSubstitution


class Fragment(Variant):
    """A protein fragment variant."""

    def __init__(self, start=None, stop=None, description=None):
        """Build a protein fragment data dictionary.

        :param start: The starting position
        :type start: None or int or str
        :param stop: The stopping position
        :type stop: None or int or str
        :param Optional[str] description: An optional description

        Example of specified fragment:

        >>> protein(name='APP', namespace='HGNC', variants=[fragment(start=672, stop=713)])

        Example of unspecified fragment:

        >>> protein(name='APP', namespace='HGNC', variants=[fragment()])
        """
        super(Fragment, self).__init__(FRAGMENT)

        if start and stop:
            self[FRAGMENT_START] = start
            self[FRAGMENT_STOP] = stop
        else:
            self[FRAGMENT_MISSING] = '?'

        if description:
            self[FRAGMENT_DESCRIPTION] = description

    def as_tuple(self):
        """Return this fragment variant as a tuple.

        :rtype: tuple
        """
        if FRAGMENT_MISSING in self:
            result = FRAGMENT, '?'
        else:
            result = FRAGMENT, (self[FRAGMENT_START], self[FRAGMENT_STOP])

        if FRAGMENT_DESCRIPTION in self:
            return result + (self[FRAGMENT_DESCRIPTION],)

        return result

    def as_bel(self):
        """Return this fragment variant as a BEL string.

        :rtype: str
        """
        if FRAGMENT_MISSING in self:
            res = '?'
        else:
            res = '{}_{}'.format(self[FRAGMENT_START], self[FRAGMENT_STOP])

        if FRAGMENT_DESCRIPTION in self:
            res += ', "{}"'.format(self[FRAGMENT_DESCRIPTION])

        return 'frag({})'.format(res)


fragment = Fragment


class Gene(CentralDogma):
    """Builds a gene node data dictionary"""

    def __init__(self, namespace, name=None, identifier=None, variants=None):
        """
        :param str namespace: The name of the database used to identify this entity
        :param str name: The database's preferred name or label for this entity
        :param variants: An optional variant or list of variants
        :type variants: None or Variant or list[Variant]
        """
        super(Gene, self).__init__(GENE, namespace, name=name, identifier=identifier, variants=variants)


gene = Gene


class _Transcribable(CentralDogma):
    """An intermediate class between the CentralDogma and rna/mirna because both of them share the ability to
    get their corresponding gene"""

    def get_gene(self):
        """Get the corresponding gene or raise an exception if it's not the reference node.

        :rtype: pybel.dsl.gene
        :raises: InferCentralDogmaException
        """
        if self.variants:
            raise InferCentralDogmaException('can not get gene for variant')

        return gene(
            namespace=self.namespace,
            name=self.name,
            identifier=self.identifier
        )


class Rna(_Transcribable):
    """Build an RNA node data dictionary."""

    def __init__(self, namespace, name=None, identifier=None, variants=None):
        """Build an RNA node data dictionary.

        :param str namespace: The name of the database used to identify this entity
        :param str name: The database's preferred name or label for this entity
        :param str identifier: The database's identifier for this entity
        :param variants: An optional variant or list of variants
        :type variants: None or Variant or list[Variant]

        Example: AKT1 protein coding gene's RNA:

        >>> rna(namespace='HGNC', name='AKT1', identifier='391')

        Non-coding RNA's can also be encoded such as `U85 <https://www-snorna.biotoul.fr/plus.php?id=U85>`_:

        >>> rna(namespace='SNORNABASE', identifer='SR0000073')
        """
        super(Rna, self).__init__(RNA, namespace, name=name, identifier=identifier, variants=variants)


rna = Rna


class MiRNA(_Transcribable):
    """Build an miRNA node data dictionary."""

    def __init__(self, namespace, name=None, identifier=None, variants=None):
        """Build an miRNA node data dictionary.

        :param str namespace: The name of the database used to identify this entity
        :param str name: The database's preferred name or label for this entity
        :param str identifier: The database's identifier for this entity
        :param variants: A list of variants
        :type variants: None or Variant or list[Variant]

        Human miRNA's are listed on HUGO's `MicroRNAs (MIR) <https://www.genenames.org/cgi-bin/genefamilies/set/476>`_
        gene family.

        MIR1-1 from `HGNC <https://www.genenames.org/cgi-bin/gene_symbol_report?hgnc_id=31499>`_:

        >>> mirna(namespace='HGNC', name='MIR1-1', identifier='31499')

        MIR1-1 from `miRBase <http://www.mirbase.org/cgi-bin/mirna_entry.pl?acc=MI0000651>`_:

        >>> mirna(namespace='MIRBASE', identifier='MI0000651')

        MIR1-1 from `Entrez Gene <https://view.ncbi.nlm.nih.gov/gene/406904>`_

        >>> mirna(namespace='ENTREZ', identifier='406904')
        """
        super(MiRNA, self).__init__(MIRNA, namespace, name=name, identifier=identifier, variants=variants)


mirna = MiRNA


class Protein(CentralDogma):
    """Build a protein node data dictionary."""

    def __init__(self, namespace, name=None, identifier=None, variants=None):
        """Build an protein node data dictionary.

        :param str namespace: The name of the database used to identify this entity
        :param str name: The database's preferred name or label for this entity
        :param str identifier: The database's identifier for this entity
        :param variants: An optional variant or list of variants
        :type variants: None or Variant or list[Variant]

        Example: AKT

        >>> protein(namespace='HGNC', name='AKT1')

        Example: AKT with optionally included HGNC database identifier

        >>> protein(namespace='HGNC', name='AKT1', identifier='391')

        Example: AKT with phosphorylation

        >>> protein(namespace='HGNC', name='AKT', variants=[pmod('Ph', code='Thr', position=308)])
        """
        super(Protein, self).__init__(PROTEIN, namespace, name=name, identifier=identifier, variants=variants)

    def get_rna(self):
        """Get the corresponding RNA or raise an exception if it's not the reference node.

        :rtype: pybel.dsl.rna
        :raises: InferCentralDogmaException
        """
        if self.variants:
            raise InferCentralDogmaException('can not get rna for variant')

        return rna(
            namespace=self.namespace,
            name=self.name,
            identifier=self.identifier
        )


protein = Protein


def _tuplable_list_as_tuple(entities):
    """Convert a reaction list to tuples.

    :type entities: iter[BaseEntity]
    :rtype: tuple[tuple]
    """
    return tuple(e.as_tuple() for e in entities)


def _entity_list_as_tuple(entities):
    """Convert a reaction list to tuples.

    :type entities: iter[BaseEntity]
    :rtype: tuple
    """
    return tuple(sorted(
        e.as_tuple()
        for e in entities
    ))


def _entity_list_as_bel(entities):  # TODO sorted?
    """Stringify a list of BEL entities.

    :type entities: iter[BaseEntity]
    :rtype: str
    """
    return ', '.join(
        str(e)
        for e in entities
    )


class Reaction(BaseEntity):
    """Build a reaction node data dictionary."""

    def __init__(self, reactants, products):
        """Build a reaction node data dictionary.

        :param list[BaseAbundance] reactants: A list of PyBEL node data dictionaries representing the reactants
        :param list[BaseAbundance] products: A list of PyBEL node data dictionaries representing the products

        Example:

        >>> reaction([protein(namespace='HGNC', name='KNG1')], [abundance(namespace='CHEBI', name='bradykinin')])
        """
        super(Reaction, self).__init__(func=REACTION)
        self.update({
            REACTANTS: reactants,
            PRODUCTS: products
        })

    def as_tuple(self):
        """Return this reaction as a tuple.

        :rtype: tuple
        """
        return self[FUNCTION], _entity_list_as_tuple(self[REACTANTS]), _entity_list_as_tuple(self[PRODUCTS])

    def as_bel(self):
        """Return this reaction as a BEL string.

        :rtype: str
        """
        return 'rxn(reactants({}), products({}))'.format(
            _entity_list_as_bel(self[REACTANTS]),
            _entity_list_as_bel(self[PRODUCTS])
        )


reaction = Reaction


class ListAbundance(BaseEntity):
    """The superclass for building list abundance (complex, abundance) node data dictionaries"""

    def __init__(self, func, members):
        """Build a list abundance node data dictionary.

        :param str func: The PyBEL function
        :param list[BaseAbundance] members: A list of PyBEL node data dictionaries
        """
        super(ListAbundance, self).__init__(func=func)
        self.update({
            MEMBERS: members,
        })

    def as_tuple(self):
        """Return this list abundance as a tuple.

        :rtype: tuple
        """
        return (self[FUNCTION],) + _entity_list_as_tuple(self[MEMBERS])

    def as_bel(self):
        """Return this list abundance as a BEL string.

        :rtype: str
        """
        return '{}({})'.format(
            rev_abundance_labels[self[FUNCTION]],
            _entity_list_as_bel(self[MEMBERS])
        )


class ComplexAbundance(ListAbundance):
    """Build a complex abundance node data dictionary with the optional ability to specify a name."""

    def __init__(self, members, namespace=None, name=None, identifier=None):
        """Build a complex list node data dictionary.

        :param list[BaseAbundance] members: A list of PyBEL node data dictionaries
        :param Optional[str] namespace: The namespace from which the name originates
        :param Optional[str] name: The name of the complex
        :param Optional[str] identifier: The identifier in the namespace in which the name originates
        """
        super(ComplexAbundance, self).__init__(func=COMPLEX, members=members)

        if namespace:
            self.update(entity(namespace=namespace, name=name, identifier=identifier))


complex_abundance = ComplexAbundance


class NamedComplexAbundance(BaseAbundance):
    """Build a named complex abundance node data dictionary."""

    def __init__(self, namespace=None, name=None, identifier=None):
        """Build a complex abundance node data dictionary.

        :param str namespace: The name of the database used to identify this entity
        :param str name: The database's preferred name or label for this entity
        :param str identifier: The database's identifier for this entity

        Example:

        >>> named_complex_abundance(namespace='SCOMP', name='Calcineurin Complex')
        """
        super(NamedComplexAbundance, self).__init__(
            func=COMPLEX,
            namespace=namespace,
            name=name,
            identifier=identifier,
        )


named_complex_abundance = NamedComplexAbundance


class CompositeAbundance(ListAbundance):
    """Build a composite abundance node data dictionary."""

    def __init__(self, members):
        """Build a composite abundance node data dictionary.

        :param list[BaseAbundance] members: A list of PyBEL node data dictionaries
        """
        super(CompositeAbundance, self).__init__(func=COMPOSITE, members=members)


composite_abundance = CompositeAbundance


@six.add_metaclass(abc.ABCMeta)
class FusionRangeBase(dict):
    """The superclass for fusion range data dictionaries"""

    @abc.abstractmethod
    def as_tuple(self):
        """Return this fusion range as a tuple.

        :rtype: tuple
        """


class MissingFusionRange(FusionRangeBase):
    """Builds a missing fusion range data dictionary"""

    def __init__(self):
        super(MissingFusionRange, self).__init__({
            FUSION_MISSING: '?'
        })

    def __str__(self):
        return '?'

    def as_tuple(self):
        """Return this fusion range as a tuple.

        :rtype: tuple
        """
        return self[FUSION_MISSING],


missing_fusion_range = MissingFusionRange


class EnumeratedFusionRange(FusionRangeBase):
    """Creates a fusion range data dictionary"""

    def __init__(self, reference, start, stop):
        """
        :param str reference: The reference code
        :param int or str start: The start position, either specified by its integer position, or '?'
        :param int or str stop: The stop position, either specified by its integer position, '?', or '*

        Example fully specified RNA fusion range:

        >>> fusion_range('r', 1, 79)

        """
        super(EnumeratedFusionRange, self).__init__({
            FUSION_REFERENCE: reference,
            FUSION_START: start,
            FUSION_STOP: stop
        })

    def as_tuple(self):
        """Return this fusion range as a tuple.

        :rtype: tuple
        """
        return (
            self[FUSION_REFERENCE],
            self[FUSION_START],
            self[FUSION_STOP]
        )

    def as_bel(self):
        """Return this fusion range as a BEL string.

        :rtype: str
        """
        return '{reference}.{start}_{stop}'.format(
            reference=self[FUSION_REFERENCE],
            start=self[FUSION_START],
            stop=self[FUSION_STOP]
        )

    def __str__(self):
        return self.as_bel()


fusion_range = EnumeratedFusionRange


class FusionBase(BaseEntity):
    """The superclass for building fusion node data dictionaries."""

    def __init__(self, func, partner_5p, partner_3p, range_5p=None, range_3p=None):
        """Build a fusion node data dictionary.

        :param str func: A PyBEL function
        :param CentralDogma partner_5p: A PyBEL node data dictionary for the 5-prime partner
        :param CentralDogma partner_3p: A PyBEL node data dictionary for the 3-prime partner
        :param Optional[FusionRangeBase] range_5p: A fusion range for the 5-prime partner
        :param Optional[FusionRangeBase] range_3p: A fusion range for the 3-prime partner
        """
        super(FusionBase, self).__init__(func=func)
        self.update({
            FUNCTION: func,
            FUSION: {
                PARTNER_5P: partner_5p,
                PARTNER_3P: partner_3p,
                RANGE_5P: range_5p or missing_fusion_range(),
                RANGE_3P: range_3p or missing_fusion_range()
            }
        })

    def as_tuple(self):
        """Return this fusion as a tuple.

        :rtype: tuple
        """
        fusion = self[FUSION]

        partner5p = fusion[PARTNER_5P][NAMESPACE], fusion[PARTNER_5P][NAME]
        partner3p = fusion[PARTNER_3P][NAMESPACE], fusion[PARTNER_3P][NAME]
        range5p = fusion[RANGE_5P].as_tuple()
        range3p = fusion[RANGE_3P].as_tuple()

        return (
            self[FUNCTION],
            partner5p,
            range5p,
            partner3p,
            range3p,
        )

    def as_bel(self):
        """Return this fusion as a BEL string

        :rtype: str
        """
        return "{}(fus({}:{}, {}, {}:{}, {}))".format(
            rev_abundance_labels[self[FUNCTION]],
            self[FUSION][PARTNER_5P][NAMESPACE],
            self[FUSION][PARTNER_5P][NAME],
            str(self[FUSION][RANGE_5P]),
            self[FUSION][PARTNER_3P][NAMESPACE],
            self[FUSION][PARTNER_3P][NAME],
            str(self[FUSION][RANGE_3P])
        )


class ProteinFusion(FusionBase):
    """Builds a protein fusion data dictionary"""

    def __init__(self, partner_5p, partner_3p, range_5p=None, range_3p=None):
        """Build a protein fusion node data dictionary.

        :param pybel.dsl.protein partner_5p: A PyBEL node data dictionary for the 5-prime partner
        :param pybel.dsl.protein partner_3p: A PyBEL node data dictionary for the 3-prime partner
        :param Optional[FusionRangeBase] range_5p: A fusion range for the 5-prime partner
        :param Optional[FusionRangeBase] range_3p: A fusion range for the 3-prime partner
        """
        super(ProteinFusion, self).__init__(
            func=PROTEIN,
            partner_5p=partner_5p,
            range_5p=range_5p,
            partner_3p=partner_3p,
            range_3p=range_3p,
        )


protein_fusion = ProteinFusion


class RnaFusion(FusionBase):
    """Builds an RNA fusion data dictionary"""

    def __init__(self, partner_5p, partner_3p, range_5p=None, range_3p=None):
        """Build an RNA fusion node data dictionary.

        :param pybel.dsl.rna partner_5p: A PyBEL node data dictionary for the 5-prime partner
        :param pybel.dsl.rna partner_3p: A PyBEL node data dictionary for the 3-prime partner
        :param Optional[FusionRangeBase] range_5p: A fusion range for the 5-prime partner
        :param Optional[FusionRangeBase] range_3p: A fusion range for the 3-prime partner

        Example, with fusion ranges using the 'r' qualifier:

        >>> rna_fusion(
        >>> ... partner_5p=rna(namespace='HGNC', name='TMPRSS2'),
        >>> ... range_5p=fusion_range('r', 1, 79),
        >>> ... partner_3p=rna(namespace='HGNC', name='ERG'),
        >>> ... range_3p=fusion_range('r', 312, 5034)
        >>> )


        Example with missing fusion ranges:

        >>> rna_fusion(
        >>> ... partner_5p=rna(namespace='HGNC', name='TMPRSS2'),
        >>> ... partner_3p=rna(namespace='HGNC', name='ERG'),
        >>> )
        """
        super(RnaFusion, self).__init__(
            func=RNA,
            partner_5p=partner_5p,
            range_5p=range_5p,
            partner_3p=partner_3p,
            range_3p=range_3p,
        )


rna_fusion = RnaFusion


class GeneFusion(FusionBase):
    """Builds a gene fusion data dictionary."""

    def __init__(self, partner_5p, partner_3p, range_5p=None, range_3p=None):
        """Build a gene fusion node data dictionary.

        :param pybel.dsl.gene partner_5p: A PyBEL node data dictionary for the 5-prime partner
        :param pybel.dsl.gene partner_3p: A PyBEL node data dictionary for the 3-prime partner
        :param Optional[FusionRangeBase] range_5p: A fusion range for the 5-prime partner
        :param Optional[FusionRangeBase] range_3p: A fusion range for the 3-prime partner

        Example, using fusion ranges with the 'c' qualifier

        >>> gene_fusion(
        >>> ... partner_5p=gene(namespace='HGNC', name='TMPRSS2'),
        >>> ... range_5p=fusion_range('c', 1, 79),
        >>> ... partner_3p=gene(namespace='HGNC', name='ERG'),
        >>> ... range_3p=fusion_range('c', 312, 5034)
        >>> )


        Example with missing fusion ranges:

        >>> gene_fusion(
        >>> ... partner_5p=gene(namespace='HGNC', name='TMPRSS2'),
        >>> ... partner_3p=gene(namespace='HGNC', name='ERG'),
        >>> )
        """
        super(GeneFusion, self).__init__(
            func=GENE,
            partner_5p=partner_5p,
            range_5p=range_5p,
            partner_3p=partner_3p,
            range_3p=range_3p,
        )


gene_fusion = GeneFusion
