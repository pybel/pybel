# -*- coding: utf-8 -*-

import abc

import six

from .exc import PyBELDSLException
from .utils import entity
from ..constants import *
from ..utils import ensure_quotes

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
        pass

    def __hash__(self):
        """Use the tuple serialization of this node as the hash"""
        return hash(self.as_tuple())


class BaseAbundance(BaseEntity):
    """The superclass for building node data dictionaries"""

    def __init__(self, func, namespace, name=None, identifier=None):
        """
        :param str func: The PyBEL function
        :param str namespace: The name of the namespace
        :param Optional[str] name:
        :param Optional[str] identifier:
        """
        if name is None and identifier is None:
            raise PyBELDSLException('Either name or identifier must be specified')

        super(BaseAbundance, self).__init__(func=func)
        self.update(entity(namespace=namespace, name=name, identifier=identifier))

    def __str__(self):
        return "{}({}:{})".format(
            rev_abundance_labels[self[FUNCTION]],
            self[NAMESPACE],
            ensure_quotes(self[NAME])
        )

    def as_tuple(self):
        """Returns this node as a PyBEL node tuple"""
        return self[FUNCTION], self[NAMESPACE], self[NAME]


class abundance(BaseAbundance):
    """Builds an abundance node data dictionary"""

    def __init__(self, namespace, name=None, identifier=None):
        """
        :param str namespace: The name of the database used to identify this entity
        :param str name: The database's preferred name or label for this entity
        :param str identifier: The database's identifier for this entity

        Example:

        >>> bioprocess(namespace='CHEBI', name='water')
        """
        super(abundance, self).__init__(ABUNDANCE, namespace=namespace, name=name, identifier=identifier)


class bioprocess(BaseAbundance):
    """Builds a biological process node data dictionary"""

    def __init__(self, namespace, name=None, identifier=None):
        """
        :param str namespace: The name of the database used to identify this entity
        :param str name: The database's preferred name or label for this entity
        :param str identifier: The database's identifier for this entity

        Example:

        >>> bioprocess(namespace='GO', name='apoptosis')
        """
        super(bioprocess, self).__init__(BIOPROCESS, namespace=namespace, name=name, identifier=identifier)


class pathology(BaseAbundance):
    """Builds a pathology node data dictionary"""

    def __init__(self, namespace, name=None, identifier=None):
        """
        :param str namespace: The name of the database used to identify this entity
        :param str name: The database's preferred name or label for this entity
        :param str identifier: The database's identifier for this entity

        Example:

        >>> pathology(namespace='DO', name='Alzheimer Disease')
        """
        super(pathology, self).__init__(PATHOLOGY, namespace=namespace, name=name, identifier=identifier)


class CentralDogma(BaseAbundance):
    """Builds a central dogma (gene, mirna, rna, protein) node data dictionary"""

    def __init__(self, func, namespace, name=None, identifier=None, variants=None):
        """
        :param str func: The PyBEL function to use
        :param str namespace: The name of the database used to identify this entity
        :param str name: The database's preferred name or label for this entity
        :param str identifier: The database's identifier for this entity
        :param list[Variant] variants: A list of variants
        """
        super(CentralDogma, self).__init__(func, namespace, name=name, identifier=identifier)
        if variants:
            self[VARIANTS] = variants

    def __str__(self):
        variants = self.get(VARIANTS)

        if not variants:
            return super(CentralDogma, self).__str__()

        variants_canon = sorted(map(str, variants))

        return "{}({}:{}, {})".format(
            rev_abundance_labels[self[FUNCTION]],
            self[NAMESPACE],
            ensure_quotes(self[NAME]),
            ', '.join(variants_canon)
        )


class Variant(dict):
    """The superclass for variant dictionaries"""

    def __init__(self, kind):
        """
        :param str kind: The kind of variant
        """
        super(Variant, self).__init__({KIND: kind})


class pmod(Variant):
    """Builds a protein modification variant dictionary"""

    def __init__(self, name, code=None, position=None, namespace=None, identifier=None):
        """
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
        super(pmod, self).__init__(PMOD)

        self[IDENTIFIER] = entity(
            namespace=(namespace or BEL_DEFAULT_NAMESPACE),
            name=name,
            identifier=identifier
        )

        if code:
            self[PMOD_CODE] = code

        if position:
            self[PMOD_POSITION] = position

    def __str__(self):
        return 'pmod({}{})'.format(
            str(self[IDENTIFIER]),
            ''.join(', {}'.format(self[x]) for x in PMOD_ORDER[2:] if x in self)
        )


class gmod(Variant):
    """Builds a gene modification variant dictionary"""

    def __init__(self, name, namespace=None, identifier=None):
        """
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
        super(gmod, self).__init__(GMOD)

        self[IDENTIFIER] = entity(
            namespace=(namespace or BEL_DEFAULT_NAMESPACE),
            name=name,
            identifier=identifier
        )

    def __str__(self):
        return 'gmod({})'.format(str(self[IDENTIFIER]))


class hgvs(Variant):
    """Builds a HGVS variant dictionary"""

    def __init__(self, variant):
        """
        :param str variant: The HGVS variant string

        Example:

        >>> protein(namespace='HGNC', name='AKT1', variants=[hgvs('p.Ala127Tyr')])
        """
        super(hgvs, self).__init__(HGVS)

        self[IDENTIFIER] = variant

    def __str__(self):
        return 'var({})'.format(self[IDENTIFIER])


class protein_substitution(hgvs):
    """Builds a HGVS variant dictionary for the given protein substitution"""

    def __init__(self, from_aa, position, to_aa):
        """
        :param str from_aa: The 3-letter amino acid code of the original residue
        :param int position: The position of the residue
        :param str to_aa: The 3-letter amino acid code of the new residue

        Example:

        >>> protein(namespace='HGNC', name='AKT1', variants=[protein_substitution('Ala', 127, 'Tyr')])
        """
        super(protein_substitution, self).__init__('p.{}{}{}'.format(from_aa, position, to_aa))


class fragment(Variant):
    def __init__(self, start=None, stop=None, description=None):
        """Make a protein fragment dictionary

        :param Optional[int or str] start: The starting position
        :param Optional[int or str] stop: The stopping position
        :param Optional[str] description: An optional description

        Example of specified fragment:

        >>> protein(name='APP', namespace='HGNC', variants=[fragment(start=672, stop=713)])

        Example of unspecified fragment:

        >>> protein(name='APP', namespace='HGNC', variants=[fragment()])
        """
        super(fragment, self).__init__(FRAGMENT)

        if start and stop:
            self[FRAGMENT_START] = start
            self[FRAGMENT_STOP] = stop
        else:
            self[FRAGMENT_MISSING] = '?'

        if description:
            self[FRAGMENT_DESCRIPTION] = description

    def __str__(self):
        if FRAGMENT_MISSING in self:
            res = '?'
        else:
            res = '{}_{}'.format(self[FRAGMENT_START], self[FRAGMENT_STOP])

        if FRAGMENT_DESCRIPTION in self:
            res += ', "{}"'.format(self[FRAGMENT_DESCRIPTION])

        return 'frag({})'.format(res)


class gene(CentralDogma):
    """Builds a gene node data dictionary"""

    def __init__(self, namespace, name=None, identifier=None, variants=None):
        """
        :param str namespace: The name of the database used to identify this entity
        :param str name: The database's preferred name or label for this entity
        :param str identifier: The database's identifier for this entity
        :param list[Variant] variants: A list of variants
        """
        super(gene, self).__init__(GENE, namespace, name=name,  identifier=identifier, variants=variants)


class rna(CentralDogma):
    """Builds an RNA node data dictionary"""

    def __init__(self, namespace, name=None, identifier=None, variants=None):
        """
        :param str namespace: The name of the database used to identify this entity
        :param str name: The database's preferred name or label for this entity
        :param str identifier: The database's identifier for this entity
        :param list[Variant] variants: A list of variants


        Example: AKT1 protein coding gene's RNA:

        >>> rna(namespace='HGNC', name='AKT1', identifier='391')

        Non-coding RNA's can also be encoded such as `U85 <https://www-snorna.biotoul.fr/plus.php?id=U85>`_:

        >>> rna(namespace='SNORNABASE', identifer='SR0000073')
        """
        super(rna, self).__init__(RNA, namespace, name=name, identifier=identifier, variants=variants)


class mirna(CentralDogma):
    """Builds a miRNA node data dictionary"""

    def __init__(self, namespace, name=None, identifier=None, variants=None):
        """
        :param str namespace: The name of the database used to identify this entity
        :param str name: The database's preferred name or label for this entity
        :param str identifier: The database's identifier for this entity
        :param list[Variant] variants: A list of variants

        Human miRNA's are listed on HUGO's `MicroRNAs (MIR) <https://www.genenames.org/cgi-bin/genefamilies/set/476>`_
        gene family.

        MIR1-1 from `HGNC <https://www.genenames.org/cgi-bin/gene_symbol_report?hgnc_id=31499>`_:

        >>> mirna(namespace='HGNC', name='MIR1-1', identifier='31499')

        MIR1-1 from `miRBase <http://www.mirbase.org/cgi-bin/mirna_entry.pl?acc=MI0000651>`_:

        >>> mirna(namespace='MIRBASE', identifier='MI0000651')

        MIR1-1 from `Entrez Gene <https://view.ncbi.nlm.nih.gov/gene/406904>`_

        >>> mirna(namespace='ENTREZ', identifier='406904')
        """
        super(mirna, self).__init__(MIRNA, namespace, name=name, identifier=identifier, variants=variants)


class protein(CentralDogma):
    """Builds a protein node data dictionary"""

    def __init__(self, namespace, name=None, identifier=None, variants=None):
        """Returns the node data dictionary for a protein

        :param str namespace: The name of the database used to identify this entity
        :param str name: The database's preferred name or label for this entity
        :param str identifier: The database's identifier for this entity
        :param list[Variant] variants: A list of variants

        Example: AKT

        >>> protein(namespace='HGNC', name='AKT1')

        Example: AKT with optionally included HGNC database identifier

        >>> protein(namespace='HGNC', name='AKT1', identifier='391')

        Example: AKT with phosphorylation

        >>> protein(namespace='HGNC', name='AKT', variants=[pmod('Ph', code='Thr', position=308)])
        """
        super(protein, self).__init__(PROTEIN, namespace, name=name, identifier=identifier, variants=variants)


def _entity_list_as_tuple(entities):
    """A helper function for converting reaction list

    :type entities: iter[BaseEntity]
    :rtype: tuple
    """
    return tuple(sorted(
        e.as_tuple()
        for e in entities
    ))


def _entity_list_as_bel(entities):  # TODO sorted?
    """A helper function for stringifying a list of BEL entities

    :type entities: iter[BaseEntity]
    :rtype: str
    """
    return ', '.join(
        str(e)
        for e in entities
    )


class reaction(BaseEntity):
    """Builds a reaction node data dictionary"""

    def __init__(self, reactants, products):
        """
        :param list[BaseAbundance] reactants: A list of PyBEL node data dictionaries representing the reactants
        :param list[BaseAbundance] products: A list of PyBEL node data dictionaries representing the products

        Example:

        >>> reaction([protein(namespace='HGNC', name='KNG1')], [abundance(namespace='CHEBI', name='bradykinin')])
        """
        super(reaction, self).__init__(func=REACTION)
        self.update({
            REACTANTS: reactants,
            PRODUCTS: products
        })

    def as_tuple(self):
        return self[FUNCTION], _entity_list_as_tuple(self[REACTANTS]), _entity_list_as_tuple(self[PRODUCTS])

    def __str__(self):
        return 'rxn(reactants({}), products({}))'.format(
            _entity_list_as_bel(self[REACTANTS]),
            _entity_list_as_bel(self[PRODUCTS])
        )


class ListAbundance(BaseEntity):
    """The superclass for building list abundance (complex, abundance) node data dictionaries"""

    def __init__(self, func, members):
        """
        :param str func: The PyBEL function
        :param list[BaseAbundance] members: A list of PyBEL node data dictionaries
        """
        super(ListAbundance, self).__init__(func=func)
        self.update({
            MEMBERS: members
        })

    def __str__(self):
        return '{}({})'.format(
            rev_abundance_labels[self[FUNCTION]],
            _entity_list_as_bel(self[MEMBERS])
        )

    def as_tuple(self):
        return (self[FUNCTION],) + _entity_list_as_tuple(self[MEMBERS])


class complex_abundance(ListAbundance):
    """Builds a complex abundance node data dictionary with the optional ability to specificy a name"""

    def __init__(self, members, namespace=None, name=None, identifier=None):
        """
        :param list[BaseAbundance] members: A list of PyBEL node data dictionaries
        :param Optional[str] namespace: The namespace from which the name originates
        :param Optional[str] name: The name of the complex
        :param Optional[str] identifier: The identifier in the namespace in which the name originates
        """
        super(complex_abundance, self).__init__(func=COMPLEX, members=members)

        if namespace:
            self.update(entity(namespace=namespace, name=name, identifier=identifier))


class composite_abundance(ListAbundance):
    """Builds a composite abundance node data dictionary"""

    def __init__(self, members):
        """
        :param list[BaseAbundance] members: A list of PyBEL node data dictionaries
        """
        super(composite_abundance, self).__init__(func=COMPOSITE, members=members)


class FusionRangeBase(dict):
    """The superclass for fusion range data dictionaries"""


class missing_fusion_range(FusionRangeBase):
    """Builds a missing fusion range data dictionary"""

    def __init__(self):
        super(missing_fusion_range, self).__init__({
            FUSION_MISSING: '?'
        })

    def __str__(self):
        return '?'

    def as_tuple(self):
        """
        :rtype: tuple
        """
        return self[FUSION_MISSING],


class fusion_range(FusionRangeBase):
    """Creates a fusion range data dictionary"""

    def __init__(self, reference, start, stop):
        """
        :param str reference: The reference code
        :param int or str start: The start position, either specified by its integer position, or '?'
        :param int or str stop: The stop position, either specified by its integer position, '?', or '*

        Example fully specified RNA fusion range:

        >>> fusion_range('r', 1, 79)

        """
        super(fusion_range, self).__init__({
            FUSION_REFERENCE: reference,
            FUSION_START: start,
            FUSION_STOP: stop
        })

    def __str__(self):
        return '{reference}.{start}_{stop}'.format(
            reference=self[FUSION_REFERENCE],
            start=self[FUSION_START],
            stop=self[FUSION_STOP]
        )

    def as_tuple(self):
        """

        :rtype: tuple
        """
        return (
            self[FUSION_REFERENCE],
            self[FUSION_START],
            self[FUSION_STOP]
        )


class FusionBase(BaseEntity):
    """The superclass for building fusion node data dictionaries"""

    def __init__(self, func, partner_5p, partner_3p, range_5p=None, range_3p=None):
        """
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

    def __str__(self):
        return "{}(fus({}:{}, {}, {}:{}, {}))".format(
            rev_abundance_labels[self[FUNCTION]],
            self[FUSION][PARTNER_5P][NAMESPACE],
            self[FUSION][PARTNER_5P][NAME],
            str(self[FUSION][RANGE_5P]),
            self[FUSION][PARTNER_3P][NAMESPACE],
            self[FUSION][PARTNER_3P][NAME],
            str(self[FUSION][RANGE_3P])
        )

    def as_tuple(self):
        """
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


class protein_fusion(FusionBase):
    """Builds a protein fusion data dictionary"""

    def __init__(self, partner_5p, partner_3p, range_5p=None, range_3p=None):
        """
        :param pybel.dsl.protein partner_5p: A PyBEL node data dictionary for the 5-prime partner
        :param pybel.dsl.protein partner_3p: A PyBEL node data dictionary for the 3-prime partner
        :param Optional[FusionRangeBase] range_5p: A fusion range for the 5-prime partner
        :param Optional[FusionRangeBase] range_3p: A fusion range for the 3-prime partner
        """
        super(protein_fusion, self).__init__(PROTEIN, partner_5p=partner_5p, range_5p=range_5p, partner_3p=partner_3p,
                                             range_3p=range_3p)


class rna_fusion(FusionBase):
    """Builds an RNA fusion data dictionary"""

    def __init__(self, partner_5p, partner_3p, range_5p=None, range_3p=None):
        """
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
        super(rna_fusion, self).__init__(RNA, partner_5p=partner_5p, range_5p=range_5p, partner_3p=partner_3p,
                                         range_3p=range_3p)


class gene_fusion(FusionBase):
    """Builds a gene fusion data dictionary"""

    def __init__(self, partner_5p, partner_3p, range_5p=None, range_3p=None):
        """
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
        super(gene_fusion, self).__init__(GENE, partner_5p=partner_5p, range_5p=range_5p, partner_3p=partner_3p,
                                          range_3p=range_3p)
