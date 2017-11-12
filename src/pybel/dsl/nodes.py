# -*- coding: utf-8 -*-

from .utils import add_identifier
from ..constants import *

__all__ = [
    'abundance',
    'gene',
    'rna',
    'mirna',
    'protein',
    'complex_abundance',
    'bioprocess',
    'pathology',
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
        raise ValueError('Either name or identifier must be specified')

    rv = {FUNCTION: func}
    add_identifier(rv, name=name, namespace=namespace, identifier=identifier)
    return rv


def pmod(name, code=None, position=None, namespace=None, identifier=None):
    """Builds a protein modification dict

    :param str name: The name of the modification
    :param str code: The three letter amino acid code for the affected residue
    :param int position: The position of the affected residue
    :param str namespace: The namespace to which the name of this modification belongs
    :param str identifier: The identifier of the name of the modification
    :rtype: dict
    """
    rv = {KIND: PMOD, IDENTIFIER: {}}
    add_identifier(rv[IDENTIFIER], name=name, namespace=(namespace or BEL_DEFAULT_NAMESPACE), identifier=identifier)

    if code:
        rv[PMOD_CODE] = code

    if position:
        rv[PMOD_POSITION] = position

    return rv


def hgvs(variant):
    """A convenience function for building a variant dictionary

    :param str variant:
    :rtype: dict
    """
    return {KIND: HGVS, IDENTIFIER: variant}


def _make_cd_abundance(func, name=None, namespace=None, identifier=None, variants=None):
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
    rv = _make_cd_abundance(GENE, name=name, namespace=namespace, identifier=identifier, variants=variants)
    return rv


def rna(name=None, namespace=None, identifier=None, variants=None):
    """Returns the node data dictionary for an RNA

    :param str namespace: The name of the database used to identify this entity
    :param str name: The database's preferred name or label for this entity
    :param str identifier: The database's identifier for this entity
    :param list variants: A list of variants
    :rtype: dict
    """
    rv = _make_cd_abundance(RNA, name=name, namespace=namespace, identifier=identifier, variants=variants)
    return rv


def mirna(name=None, namespace=None, identifier=None, variants=None):
    """Returns the node data dictionary for a miRNA

    :param str namespace: The name of the database used to identify this entity
    :param str name: The database's preferred name or label for this entity
    :param str identifier: The database's identifier for this entity
    :param list variants: A list of variants
    :rtype: dict
    """
    rv = _make_cd_abundance(MIRNA, name=name, namespace=namespace, identifier=identifier, variants=variants)
    return rv


def protein(name=None, namespace=None, identifier=None, variants=None):
    """Returns the node data dictionary for a protein

    :param str namespace: The name of the database used to identify this entity
    :param str name: The database's preferred name or label for this entity
    :param str identifier: The database's identifier for this entity
    :param list variants: A list of variants
    :rtype: dict
    """
    rv = _make_cd_abundance(PROTEIN, name=name, namespace=namespace, identifier=identifier, variants=variants)
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
    """
    return _make_abundance(PATHOLOGY, name=name, namespace=namespace, identifier=identifier)


def complex_abundance(members, namespace=None, name=None, identifier=None):
    """Returns the node data dictionary for a protein complex

    :param list[dict] members: A list of PyBEL node data dictionaries
    :param str namespace: The namespace from which the name originates
    :param str name: The name of the complex
    :param str identifier: The identifier in the namespace in which the name originates
    :rtype: dict
    """
    rv = {
        FUNCTION: COMPLEX,
        MEMBERS: members
    }

    if namespace and name:
        add_identifier(rv, name=name, namespace=namespace, identifier=identifier)

    return rv


def fusion_range(reference, start, stop):
    return {
        FUSION_REFERENCE: reference,
        FUSION_START: start,
        FUSION_STOP: stop

    }


def fusion(func, partner_5p, range_5p, partner_3p, range_3p):
    """

    :param str func: A PyBEL function
    :param dict partner_5p: A PyBEL node data dictionary
    :param dict range_5p:
    :param dict partner_3p: A fusion range produced by :func:`fusion_range`
    :param dict range_3p: A fusion range produced by :func:`fusion_range`
    :return:
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
