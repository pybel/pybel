# -*- coding: utf-8 -*-

"""

This module contains the database models that support the PyBEL definition cache and graph cache

"""

import datetime

from sqlalchemy import Column, ForeignKey, Table, UniqueConstraint
from sqlalchemy import Integer, String, DateTime, Text, Date, Binary, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from ..constants import CITATION_REFERENCE, CITATION_TYPE, METADATA_VERSION, METADATA_NAME

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

CITATION_TABLE_NAME = 'pybel_citation'
EVIDENCE_TABLE_NAME = 'pybel_evidence'
NETWORK_EDGE_TABLE_NAME = 'pybel_network_edge'
NETWORK_TABLE_NAME = 'pybel_network'
NODE_TABLE_NAME = 'pybel_node'
EDGE_TABLE_NAME = 'pybel_edge'
AUTHOR_TABLE_NAME = 'pybel_author'
AUTHOR_CITATION_TABLE_NAME = 'pybel_author_citation'
EDGE_ANNOTATION_TABLE_NAME = 'pybel_edge_annotationEntry'

Base = declarative_base()


class Namespace(Base):
    """Represents a BEL Namespace"""
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
    """Represents a name within a BEL namespace"""
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
    """Represents a BEL Annotation"""
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
    """Represents a value within a BEL Annotation"""
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
    """Represents an OWL Namespace"""
    __tablename__ = OWL_NAMESPACE_TABLE_NAME

    id = Column(Integer, primary_key=True)
    iri = Column(Text, unique=True)

    entries = relationship('OwlNamespaceEntry', back_populates='owl')


class OwlNamespaceEntry(Base):
    """Represents a name within an OWL Namespace"""
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
    """Represents an OWL namespace used as an annotation"""
    __tablename__ = OWL_ANNOTATION_TABLE_NAME

    id = Column(Integer, primary_key=True)
    iri = Column(Text, unique=True)

    entries = relationship('OwlAnnotationEntry', back_populates='owl')


class OwlAnnotationEntry(Base):
    """Represents a name in an OWL namespace used as an annotation"""
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


network_edge = Table(
    NETWORK_EDGE_TABLE_NAME, Base.metadata,
    Column('network_id', Integer, ForeignKey('{}.id'.format(NETWORK_TABLE_NAME)), primary_key=True),
    Column('edge_id', Integer, ForeignKey('{}.id'.format(EDGE_TABLE_NAME)), primary_key=True)
)

author_citation = Table(
    AUTHOR_CITATION_TABLE_NAME, Base.metadata,
    Column('author_id', Integer, ForeignKey('{}.id'.format(AUTHOR_TABLE_NAME))),
    Column('citation_id', Integer, ForeignKey('{}.id'.format(CITATION_TABLE_NAME)))
)

edge_annotation = Table(
    EDGE_ANNOTATION_TABLE_NAME, Base.metadata,
    Column('edge_id', Integer, ForeignKey('{}.id'.format(EDGE_TABLE_NAME)), primary_key=True),
    Column('annotationEntry_id', Integer, ForeignKey('{}.id'.format(ANNOTATION_ENTRY_TABLE_NAME)), primary_key=True)
)


class Network(Base):
    """Represents a collection of edges, specified by a BEL Script"""
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

    edges = relationship('Edge', secondary=network_edge)

    __table_args__ = (
        UniqueConstraint(METADATA_NAME, METADATA_VERSION),
    )


class Node(Base):
    """Represents a BEL Term"""
    __tablename__ = NODE_TABLE_NAME

    id = Column(Integer, primary_key=True)

    bel = Column(String, nullable=False)
    blob = Column(Binary)


class Edge(Base):
    """Represents the relation between two BEL terms and its properties"""
    __tablename__ = EDGE_TABLE_NAME

    id = Column(Integer, primary_key=True)

    source_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)))
    source = relationship('Node', foreign_keys=[source_id])

    target_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)))
    target = relationship('Node', foreign_keys=[target_id])

    evidence_id = Column(Integer, ForeignKey('{}.id'.format(EVIDENCE_TABLE_NAME)))
    evidence = relationship("Evidence")

    annotations = relationship('AnnotationEntry', secondary=edge_annotation)

    relation = Column(String, nullable=False)
    bel = Column(String, nullable=False)
    blob = Column(Binary)


class Evidence(Base):
    """Represents a piece of support taken from a Publication"""
    __tablename__ = EVIDENCE_TABLE_NAME
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False, index=True)

    citation_id = Column(Integer, ForeignKey('{}.id'.format(CITATION_TABLE_NAME)))
    citation = relationship('Citation')


class Citation(Base):
    """The information about the citations that are used to prove a specific relation are stored in this table."""
    __tablename__ = CITATION_TABLE_NAME

    id = Column(Integer, primary_key=True)
    type = Column(String(16), nullable=False)
    name = Column(String(255), nullable=False)
    reference = Column(String(255), nullable=False)
    date = Column(Date, nullable=True)
    comments = Column(String(255), nullable=True)

    authors = relationship("Author", secondary=author_citation)

    __table_args__ = (
        UniqueConstraint(CITATION_TYPE, CITATION_REFERENCE),
    )


class Author(Base):
    """Represents an Author of a publication"""
    __tablename__ = AUTHOR_TABLE_NAME

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)

    citations = relationship("Citation", secondary=author_citation)
