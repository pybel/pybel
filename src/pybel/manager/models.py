# -*- coding: utf-8 -*-

"""
This module contains the database models that support the PyBEL definition cache and graph cache
"""

import datetime

from sqlalchemy import Column, ForeignKey, Table, UniqueConstraint
from sqlalchemy import Integer, String, DateTime, Text, Date, Binary, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

NAMESPACE_TABLE_NAME = 'pybel_namespace'
NAMESPACE_ENTRY_TABLE_NAME = 'pybel_namespaceEntry'
ANNOTATION_TABLE_NAME = 'pybel_annotation'
ANNOTATION_ENTRY_TABLE_NAME = 'pybel_annotationEntry'

OWL_NAMESPACE_TABLE_NAME = 'pybel_owlNamespace'
OWL_NAMESPACE_ENTRY_TABLE_NAME = 'pybel_owlNamespaceEntry'
OWL_ANNOTATION_TABLE_NAME = 'pybel_owlAnnotation'
OWL_ANNOTATION_ENTRY_TABLE_NAME = 'pybel_owlAnnotationEntry'

NAMESPACE_EQUIVALENCE_CLASS_TABLE_NAME = 'pybel_namespaceEquivalenceClass'
NAMESPACE_EQUIVALENCE_TABLE_NAME = 'pybel_namespaceEquivalence'

NETWORK_TABLE_NAME = 'pybel_network'

Base = declarative_base()


class Namespace(Base):
    __tablename__ = NAMESPACE_TABLE_NAME
    id = Column(Integer, primary_key=True)

    url = Column(String(255))
    keyword = Column(String(8), index=True)
    name = Column(String(255))
    domain = Column(String(255))
    species = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)
    version = Column(String(255), nullable=True)
    created = Column(DateTime)
    query_url = Column(Text, nullable=True)

    author = Column(String(255))
    license = Column(String(255), nullable=True)
    contact = Column(String(255), nullable=True)

    citation = Column(String(255))
    citation_description = Column(String(255), nullable=True)
    citation_version = Column(String(255), nullable=True)
    citation_published = Column(Date, nullable=True)
    citation_url = Column(String(255), nullable=True)

    entries = relationship('NamespaceEntry', back_populates="namespace")

    has_equivalences = Column(Boolean, default=False)


class NamespaceEntry(Base):
    __tablename__ = NAMESPACE_ENTRY_TABLE_NAME
    id = Column(Integer, primary_key=True)

    name = Column(String(255), nullable=False)
    encoding = Column(String(8), nullable=True)

    namespace_id = Column(Integer, ForeignKey(NAMESPACE_TABLE_NAME + '.id'), index=True)
    namespace = relationship('Namespace', back_populates='entries')

    equivalence_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_EQUIVALENCE_CLASS_TABLE_NAME)), nullable=True)
    equivalence = relationship('NamespaceEntryEquivalence', back_populates='members')


class NamespaceEntryEquivalence(Base):
    __tablename__ = NAMESPACE_EQUIVALENCE_CLASS_TABLE_NAME
    id = Column(Integer, primary_key=True)
    label = Column(String(255), nullable=False, unique=True, index=True)

    members = relationship('NamespaceEntry', back_populates='equivalence')


class Annotation(Base):
    __tablename__ = ANNOTATION_TABLE_NAME

    id = Column(Integer, primary_key=True)

    url = Column(String(255))
    keyword = Column(String(50), index=True)
    type = Column(String(255))
    description = Column(String(255), nullable=True)
    usage = Column(Text, nullable=True)
    version = Column(String(255), nullable=True)
    created = Column(DateTime)

    name = Column(String(255))
    author = Column(String(255))
    license = Column(String(255), nullable=True)
    contact = Column(String(255), nullable=True)

    citation = Column(String(255))
    citation_description = Column(String(255), nullable=True)
    citation_version = Column(String(255), nullable=True)
    citation_published = Column(Date, nullable=True)
    citation_url = Column(String(255), nullable=True)

    entries = relationship('AnnotationEntry', back_populates="annotation")


class AnnotationEntry(Base):
    __tablename__ = ANNOTATION_ENTRY_TABLE_NAME
    id = Column(Integer, primary_key=True)

    name = Column(String(255), nullable=False)
    label = Column(String(255), nullable=True)

    annotation_id = Column(Integer, ForeignKey(ANNOTATION_TABLE_NAME + '.id'), index=True)
    annotation = relationship('Annotation', back_populates='entries')


owl_namespace_relationship = Table(
    'owl_namespace_relationship', Base.metadata,
    Column('left_id', Integer, ForeignKey('{}.id'.format(OWL_NAMESPACE_ENTRY_TABLE_NAME)), primary_key=True),
    Column('right_id', Integer, ForeignKey('{}.id'.format(OWL_NAMESPACE_ENTRY_TABLE_NAME)), primary_key=True)
)


class OwlNamespace(Base):
    __tablename__ = OWL_NAMESPACE_TABLE_NAME

    id = Column(Integer, primary_key=True)
    iri = Column(Text, unique=True)

    entries = relationship('OwlNamespaceEntry', back_populates='owl')


class OwlNamespaceEntry(Base):
    __tablename__ = OWL_NAMESPACE_ENTRY_TABLE_NAME

    id = Column(Integer, primary_key=True)

    entry = Column(String(255))
    encoding = Column(String(50))

    owl_id = Column(Integer, ForeignKey('{}.id'.format(OWL_NAMESPACE_TABLE_NAME)), index=True)
    owl = relationship('OwlNamespace', back_populates='entries')

    children = relationship('OwlNamespaceEntry',
                            secondary=owl_namespace_relationship,
                            primaryjoin=id == owl_namespace_relationship.c.left_id,
                            secondaryjoin=id == owl_namespace_relationship.c.right_id)


owl_annotation_relationship = Table(
    'owl_annotation_relationship', Base.metadata,
    Column('left_id', Integer, ForeignKey('{}.id'.format(OWL_ANNOTATION_ENTRY_TABLE_NAME)), primary_key=True),
    Column('right_id', Integer, ForeignKey('{}.id'.format(OWL_ANNOTATION_ENTRY_TABLE_NAME)), primary_key=True)
)


class OwlAnnotation(Base):
    __tablename__ = OWL_ANNOTATION_TABLE_NAME

    id = Column(Integer, primary_key=True)
    iri = Column(Text, unique=True)

    entries = relationship('OwlAnnotationEntry', back_populates='owl')


class OwlAnnotationEntry(Base):
    __tablename__ = OWL_ANNOTATION_ENTRY_TABLE_NAME

    id = Column(Integer, primary_key=True)

    entry = Column(String(255))
    label = Column(String(255))

    owl_id = Column(Integer, ForeignKey('{}.id'.format(OWL_ANNOTATION_TABLE_NAME)), index=True)
    owl = relationship('OwlAnnotation', back_populates='entries')

    children = relationship('OwlAnnotationEntry',
                            secondary=owl_annotation_relationship,
                            primaryjoin=id == owl_annotation_relationship.c.left_id,
                            secondaryjoin=id == owl_annotation_relationship.c.right_id)


class Network(Base):
    __tablename__ = NETWORK_TABLE_NAME
    id = Column(Integer, primary_key=True)

    name = Column(String(255), index=True)
    version = Column(String(255))

    authors = Column(Text, nullable=True)
    contact = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    copyright = Column(String(255), nullable=True)
    disclaimer = Column(String(255), nullable=True)
    licenses = Column(String(255), nullable=True)

    created = Column(DateTime, default=datetime.datetime.utcnow)
    blob = Column(Binary)

    __table_args__ = (
        UniqueConstraint("name", "version"),
    )
