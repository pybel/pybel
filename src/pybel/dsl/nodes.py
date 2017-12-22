# -*- coding: utf-8 -*-

from .exc import PyBELDSLException
from .utils import entity
from ..constants import *

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
    'fragment',
    'fusion_range',
    'missing_fusion_range',
    'protein_fusion',
    'rna_fusion',
    'gene_fusion',
]


def _make_abundance(func, namespace, name=None, identifier=None):
    """

    :param str func: The PyBEL function
    :param str namespace: The name of the namespace
    :param Optional[str] name:
    :param Optional[str] identifier:
    :return:
    """
    if name is None and identifier is None:
        raise PyBELDSLException('Either name or identifier must be specified')

    rv = {FUNCTION: func}
    rv.update(entity(namespace=namespace, name=name, identifier=identifier))
    return rv


def pmod(name, code=None, position=None, namespace=None, identifier=None):
    """Builds a protein modification dict

    :param str name: The name of the modification
    :param str code: The three letter amino acid code for the affected residue. Capital first letter.
    :param int position: The position of the affected residue
    :param str namespace: The namespace to which the name of this modification belongs
    :param str identifier: The identifier of the name of the modification
    :rtype: dict

    Example from BEL default namespace:

    >>> pmod('Ph', code='Thr', position=308)

    Example from custom namespace:

    >>> pmod(name='protein phosphorylation', namespace='GO', code='Thr', position=308)

    Example from custom namespace additionally qualified with identifier:

    >>> pmod(name='protein phosphorylation', namespace='GO', identifier='GO:0006468', code='Thr', position=308)
    """
    rv = {
        KIND: PMOD,
        IDENTIFIER: entity(
            namespace=(namespace or BEL_DEFAULT_NAMESPACE),
            name=name,
            identifier=identifier
        )
    }

    if code:
        rv[PMOD_CODE] = code

    if position:
        rv[PMOD_POSITION] = position

    return rv


def gmod(name, namespace=None, identifier=None):
    """Builds a gene modification dict

    :param str name: The name of the gene modification
    :param Optional[str] namespace: The namespace of the gene modification
    :param Optional[str] identifier: The identifier of the name in the database

    Example from BEL default namespace:

    >>> gmod('Me')

    Example from custom namespace:

    >>> gmod(name='DNA methylation', namespace='GO', identifier='GO:0006306',)
    """
    rv = {
        KIND: GMOD,
        IDENTIFIER: entity(
            namespace=(namespace or BEL_DEFAULT_NAMESPACE),
            name=name,
            identifier=identifier
        )
    }

    return rv


def hgvs(variant):
    """A convenience function for building a variant dictionary

    :param str variant: The HGVS variant string
    :rtype: dict

    Example:

    >>> protein(namespace='HGNC', name='AKT1', variants=[hgvs('p.Ala127Tyr')])
    """
    return {KIND: HGVS, IDENTIFIER: variant}


def fragment(start=None, stop=None, description=None):
    """Make a protein fragment dictionary

    :param Optional[int or str] start: The starting position
    :param Optional[int or str] stop: The stopping position
    :param Optional[str] description: An optional description
    :rtype: dict

    Example of specified fragment:

    >>> protein(name='APP', namespace='HGNC', variants=[fragment(start=672, stop=713)])

    Example of unspecified fragment:

    >>> protein(name='APP', namespace='HGNC', variants=[fragment()])
    """
    rv = {KIND: FRAGMENT}

    if start and stop:
        rv[FRAGMENT_START] = start
        rv[FRAGMENT_STOP] = stop
    else:
        rv[FRAGMENT_MISSING] = '?'

    if description:
        rv[FRAGMENT_DESCRIPTION] = description

    return rv


def _make_central_dogma_abundance(func, name=None, namespace=None, identifier=None, variants=None):
    """Make central dogma abundance (meaning it can have variants)"""
    rv = _make_abundance(func, name=name, namespace=namespace, identifier=identifier)

    if variants:
        rv[VARIANTS] = variants

    return rv


def gene(name=None, namespace=None, identifier=None, variants=None):
    """Returns the node data dictionary for a gene

    :param str namespace: The name of the database used to identify this entity
    :param str name: The database's preferred name or label for this entity
    :param str identifier: The database's identifier for this entity
    :param list variants: A list of variants
    :rtype: dict
    """
    rv = _make_central_dogma_abundance(GENE, name=name, namespace=namespace, identifier=identifier, variants=variants)
    return rv


def rna(name=None, namespace=None, identifier=None, variants=None):
    """Returns the node data dictionary for an RNA

    :param str namespace: The name of the database used to identify this entity
    :param str name: The database's preferred name or label for this entity
    :param str identifier: The database's identifier for this entity
    :param list variants: A list of variants
    :rtype: dict
    """
    rv = _make_central_dogma_abundance(RNA, name=name, namespace=namespace, identifier=identifier, variants=variants)
    return rv


def mirna(name=None, namespace=None, identifier=None, variants=None):
    """Returns the node data dictionary for a miRNA

    :param str namespace: The name of the database used to identify this entity
    :param str name: The database's preferred name or label for this entity
    :param str identifier: The database's identifier for this entity
    :param list variants: A list of variants
    :rtype: dict
    """
    rv = _make_central_dogma_abundance(MIRNA, name=name, namespace=namespace, identifier=identifier, variants=variants)
    return rv


def protein(name=None, namespace=None, identifier=None, variants=None):
    """Returns the node data dictionary for a protein

    :param str namespace: The name of the database used to identify this entity
    :param str name: The database's preferred name or label for this entity
    :param str identifier: The database's identifier for this entity
    :param list variants: A list of variants
    :rtype: dict

    Example: AKT

    >>> protein(namespace='HGNC', name='AKT1')

    Example: AKT with optionally included HGNC database identifier

    >>> protein(namespace='HGNC', name='AKT1', identifier='391')

    Example: AKT with phosphorylation

    >>> protein(namespace='HGNC', name='AKT', variants=[pmod('Ph', code='Thr', position=308)])
    """
    rv = _make_central_dogma_abundance(PROTEIN, name=name, namespace=namespace, identifier=identifier,
                                       variants=variants)
    return rv


def abundance(namespace, name=None, identifier=None):
    """Returns the node data dictionary for an abundance

    :param str namespace: The name of the database used to identify this entity
    :param str name: The database's preferred name or label for this entity
    :param str identifier: The database's identifier for this entity
    :rtype: dict
    """
    return _make_abundance(ABUNDANCE, name=name, namespace=namespace, identifier=identifier)


def bioprocess(namespace, name=None, identifier=None):
    """Returns the node data dictionary for a biological process

    :param str namespace: The name of the database used to identify this entity
    :param str name: The database's preferred name or label for this entity
    :param str identifier: The database's identifier for this entity
    :rtype: dict
    """
    return _make_abundance(BIOPROCESS, name=name, namespace=namespace, identifier=identifier)


def pathology(namespace, name=None, identifier=None):
    """Returns the node data dictionary for a pathology

    :param str namespace: The name of the database used to identify this entity
    :param str name: The database's preferred name or label for this entity
    :param str identifier: The database's identifier for this entity
    :rtype: dict

    Example:

    >>> pathology(namespace='DO', name='Alzheimer Disease')
    """
    return _make_abundance(PATHOLOGY, name=name, namespace=namespace, identifier=identifier)


def reaction(reactants, products):
    """Creates a reaction data dictionary

    :param list[dict] reactants: A list of PyBEL node data dictionaries representing the reactants
    :param list[dict] products: A list of PyBEL node data dictionaries representing the products
    :rtype: dict

    Example:

    >>> reaction([protein(namespace='HGNC', name='KNG1')], [abundance(namespace='CHEBI', name='bradykinin')])
    """
    rv = {
        FUNCTION: REACTION,
        REACTANTS: reactants,
        PRODUCTS: products
    }
    return rv


def complex_abundance(members, namespace=None, name=None, identifier=None):
    """Returns the node data dictionary for a complex, with optional ability to specify a name

    :param list[dict] members: A list of PyBEL node data dictionaries
    :param Optional[str] namespace: The namespace from which the name originates
    :param Optional[str] name: The name of the complex
    :param Optional[str] identifier: The identifier in the namespace in which the name originates
    :rtype: dict
    """
    rv = {
        FUNCTION: COMPLEX,
        MEMBERS: members
    }

    if namespace:
        rv.update(entity(namespace=namespace, name=name, identifier=identifier))

    return rv


def composite_abundance(members):
    """Returns the node data dictionary for a composite

    :param list[dict] members: A list of PyBEL node data dictionaries
    :rtype: dict
    """
    rv = {
        FUNCTION: COMPOSITE,
        MEMBERS: members
    }

    return rv


def missing_fusion_range():
    """Creates a missing fusion range

    :rtype: dict
    """
    return {
        FUSION_MISSING: '?'
    }


def fusion_range(reference, start, stop):
    """Creates a fusion range

    :param reference:
    :param start:
    :param stop:
    :rtype: dict
    """
    return {
        FUSION_REFERENCE: reference,
        FUSION_START: start,
        FUSION_STOP: stop
    }


def fusion(func, partner_5p, range_5p, partner_3p, range_3p):
    """Creates a fusion entry

    :param str func: A PyBEL function
    :param dict partner_5p: A PyBEL node data dictionary for the 5-prime partner
    :param dict range_5p: A fusion range produced by :func:`fusion_range` for the 5-prime partner
    :param dict partner_3p: A PyBEL node data dictionary for the 3-prime partner
    :param dict range_3p: A fusion range produced by :func:`fusion_range` for the 3-prime partner
    :rtype: dict
    """
    return {
        FUNCTION: func,
        FUSION: {
            PARTNER_5P: partner_5p,
            PARTNER_3P: partner_3p,
            RANGE_5P: range_5p,
            RANGE_3P: range_3p
        }
    }


def protein_fusion(partner_5p, range_5p, partner_3p, range_3p):
    """Creates a protein fusion

    :param dict partner_5p: A PyBEL node data dictionary for the 5-prime partner
    :param dict range_5p: A fusion range produced by :func:`fusion_range` for the 5-prime partner
    :param dict partner_3p: A PyBEL node data dictionary for the 3-prime partner
    :param dict range_3p: A fusion range produced by :func:`fusion_range` for the 3-prime partner
    :rtype: dict
    """
    return fusion(PROTEIN, partner_5p=partner_5p, range_5p=range_5p, partner_3p=partner_3p, range_3p=range_3p)


def rna_fusion(partner_5p, range_5p, partner_3p, range_3p):
    """Creates a RNA fusion

    :param dict partner_5p: A PyBEL node data dictionary for the 5-prime partner
    :param dict range_5p: A fusion range produced by :func:`fusion_range` for the 5-prime partner
    :param dict partner_3p: A PyBEL node data dictionary for the 3-prime partner
    :param dict range_3p: A fusion range produced by :func:`fusion_range` for the 3-prime partner
    :rtype: dict
    """
    return fusion(RNA, partner_5p=partner_5p, range_5p=range_5p, partner_3p=partner_3p, range_3p=range_3p)


def gene_fusion(partner_5p, range_5p, partner_3p, range_3p):
    """Creates a gene fusion

    :param dict partner_5p: A PyBEL node data dictionary for the 5-prime partner
    :param dict range_5p: A fusion range produced by :func:`fusion_range` for the 5-prime partner
    :param dict partner_3p: A PyBEL node data dictionary for the 3-prime partner
    :param dict range_3p: A fusion range produced by :func:`fusion_range` for the 3-prime partner
    :rtype: dict
    """
    return fusion(GENE, partner_5p=partner_5p, range_5p=range_5p, partner_3p=partner_3p, range_3p=range_3p)
