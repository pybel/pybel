# -*- coding: utf-8 -*-

"""

This module contains the database models that support the PyBEL definition cache and graph cache

"""

import datetime

from sqlalchemy import Column, ForeignKey, Table, UniqueConstraint
from sqlalchemy import Integer, String, DateTime, Text, Date, Binary, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from ..constants import *

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
CITATION_TABLE_NAME = 'pybel_citation'
EVIDENCE_TABLE_NAME = 'pybel_evidence'
EDGE_TABLE_NAME = 'pybel_edge'
NODE_TABLE_NAME = 'pybel_node'
MODIFICATION_TABLE_NAME = 'pybel_modification'
PROPERTY_TABLE_NAME = 'pybel_property'
AUTHOR_TABLE_NAME = 'pybel_author'
AUTHOR_CITATION_TABLE_NAME = 'pybel_author_citation'
EDGE_PROPERTY_TABLE_NAME = 'pybel_edge_property'
NODE_MODIFICATION_TABLE_NAME = 'pybel_node_modification'
EDGE_ANNOTATION_TABLE_NAME = 'pybel_edge_annotationEntry'
NETWORK_EDGE_TABLE_NAME = 'pybel_network_edge'

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

    def forGraph(self):
        return {NAMESPACE: self.namespace.keyword, NAME: self.name}


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

    def forGraph(self):
        return {self.annotation.keyword: self.name}


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


node_modification = Table(
    NODE_MODIFICATION_TABLE_NAME, Base.metadata,
    Column('node_id', Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME))),
    Column('modification_id', Integer, ForeignKey('{}.id'.format(MODIFICATION_TABLE_NAME)))
)


class Node(Base):
    """Represents a BEL Term"""
    __tablename__ = NODE_TABLE_NAME

    id = Column(Integer, primary_key=True)

    type = Column(String(255), nullable=False)
    namespaceEntry_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_ENTRY_TABLE_NAME)), nullable=True)
    namespaceEntry = relationship('NamespaceEntry', foreign_keys=[namespaceEntry_id])
    namespacePattern = Column(String(255), nullable=True)
    modification = Column(Boolean, default=False)

    bel = Column(String, nullable=False)
    blob = Column(Binary)

    modifications = relationship("Modification", secondary=node_modification)

    def forGraph(self):
        node_key = [self.type]
        node_data = {
            FUNCTION: self.type,
        }
        if self.namespaceEntry:
            namespace_entry = self.namespaceEntry.forGraph()
            node_data.update(namespace_entry)
            node_key.append(namespace_entry[NAMESPACE])
            node_key.append(namespace_entry[NAME])

        if self.type == FUSION:
            fus = self.modifications[0].forGraph()
            node_data.update(fus[-1])
            del (fus[-1])
            for entry in fus:
                node_key.append(entry)

        elif self.modification:
            node_data[VARIANTS] = []
            for mod in self.modifications:
                mod_tuple = tuple(mod.forGraph())
                node_data[VARIANTS].append(mod_tuple)
                node_key.append(mod_tuple)
            node_data[VARIANTS] = tuple(node_data[VARIANTS])

        return {'key': tuple(node_key), 'data': node_data}


class Modification(Base):
    """The modifications that are present in the network are stored in this table."""

    __tablename__ = MODIFICATION_TABLE_NAME
    id = Column(Integer, primary_key=True)

    modType = Column(String(255))
    variantString = Column(String, nullable=True)

    p3PartnerName_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_ENTRY_TABLE_NAME)), nullable=True)
    p3Partner = relationship("NamespaceEntry", foreign_keys=[p3PartnerName_id])

    p3Reference = Column(String(10), nullable=True)
    p3Start = Column(String(255), nullable=True)
    p3Stop = Column(String(255), nullable=True)
    p3Missing = Column(String(10), nullable=True)
    # p3Range = Column(String(255), nullable=True)

    p5PartnerName_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_ENTRY_TABLE_NAME)), nullable=True)
    p5Partner = relationship("NamespaceEntry", foreign_keys=[p5PartnerName_id])

    p5Reference = Column(String(10), nullable=True)
    p5Start = Column(String(255), nullable=True)
    p5Stop = Column(String(255), nullable=True)
    p5Missing = Column(String(10), nullable=True)
    # p5Range = Column(String(255), nullable=True)

    modName = Column(String(255), nullable=True)
    aminoA = Column(String(3), nullable=True)
    position = Column(Integer, nullable=True)

    nodes = relationship("Node", secondary=node_modification)

    def forGraph(self):
        mod_dict = {KIND: self.modType}
        if self.pmodName:
            mod_dict[IDENTIFIER] = {
                NAMESPACE: 'PYBEL',
                NAME: self.pmodName
            }
        if self.aminoA:
            mod_dict['code'] = self.aminoA
        if self.position:
            mod_dict['pos'] = self.position

        return mod_dict

    def old_forGraph(self):
        mod_array = [self.modType]

        if self.modType == 'ProteinFusion':
            mod_dict = {}
            if self.p5Partner:
                p5 = self.p5Partner.forGraph()
                mod_array.append((p5['namespace'], p5['name']))
                mod_dict['partner_5p'] = p5
            if self.p5range:
                mod_array.append((self.p5Range,))
                mod_dict['range_5p'] = (self.p5Range,)
            if self.p3Partner:
                p3 = self.p3Partner.forGraph()
                mod_array.append((p3['namespace'], p3['name']))
                mod_dict['partner_3p'] = p3
            if self.p3Range:
                mod_array.append((self.p3Range,))
                mod_dict['range_3p'] = (self.p3Range,)
            mod_array.append(mod_dict)

        elif self.modType == 'ProteinModification':
            mod_array.append(self.pmodName)
            if self.aminoA:
                mod_array.append(self.aminoA)
            if self.position:
                mod_array.append(self.position)

        elif self.modType in ('Variant', 'GeneModificaiton'):
            mod_array.append(self.variantString)

        return mod_array

author_citation = Table(
    AUTHOR_CITATION_TABLE_NAME, Base.metadata,
    Column('author_id', Integer, ForeignKey('{}.id'.format(AUTHOR_TABLE_NAME))),
    Column('citation_id', Integer, ForeignKey('{}.id'.format(CITATION_TABLE_NAME)))
)


class Author(Base):
    """Contains all author names."""

    __tablename__ = AUTHOR_TABLE_NAME
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)

    citations = relationship("Citation", secondary=author_citation)



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


    def forGraph(self):
        citation_dict = {
            CITATION_NAME: self.name,
            CITATION_REFERENCE: self.reference,
            CITATION_TYPE: self.type
        }
        if self.authors:
            citation_dict[CITATION_AUTHORS] = "|".join([author for author in self.authors])
        if self.date:
            citation_dict[CITATION_DATE] = self.date
        if self.comments:
            citation_dict[CITATION_COMMENTS] = self.comments

        return citation_dict


class Evidence(Base):
    """This table contains the evidence text that proves a specific relationship and refers the source that is cited."""

    __tablename__ = EVIDENCE_TABLE_NAME
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False, index=True)

    citation_id = Column(Integer, ForeignKey('{}.id'.format(CITATION_TABLE_NAME)))
    citation = relationship('Citation')

    def __repr__(self):
        return '{}'.format(self.text)

    def forGraph(self):
        return {
            CITATION: self.citation.forGraph(),
            EVIDENCE: self.text
        }


edge_property = Table(
    EDGE_PROPERTY_TABLE_NAME, Base.metadata,
    Column('edge_id', Integer, ForeignKey('{}.id'.format(EDGE_TABLE_NAME))),
    Column('property_id', Integer, ForeignKey('{}.id'.format(PROPERTY_TABLE_NAME)))
)


class Edge(Base):
    """Relationships are represented in this table. It shows the nodes that are in a relation to eachother and provides
    information about the context of the relation by refaring to the annotation, property and evidence tables."""

    __tablename__ = EDGE_TABLE_NAME

    id = Column(Integer, primary_key=True)

    graphIdentifier = Column(Integer)
    bel = Column(String, nullable=False)
    relation = Column(String, nullable=False)

    source_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)))
    source = relationship('Node', foreign_keys=[source_id])

    target_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)))
    target = relationship('Node', foreign_keys=[target_id])

    evidence_id = Column(Integer, ForeignKey('{}.id'.format(EVIDENCE_TABLE_NAME)))
    evidence = relationship("Evidence")

    annotations = relationship('AnnotationEntry', secondary=edge_annotation)
    properties = relationship('Property', secondary=edge_property)

    blob = Column(Binary)

    def forGraph(self):
        source_node = self.source.forGraph()
        target_node = self.target.forGraph()
        edge_dict = {
            'source': {
                'node': (source_node['key'], source_node['data']),
                'key': source_node['key']
            },
            'target': {
                'node': (target_node['key'], target_node['data']),
                'key': target_node['key']
            },
            'data': {
                'relation': self.relation,
            },
            'key': self.graphIdentifier
        }
        edge_dict['data'].update(self.evidence.forGraph())
        for anno in self.annotations:
            edge_dict['data'].update(anno.forGraph())
        for prop in self.properties:
            prop_info = prop.forGraph()
            if prop_info['participant'] in edge_dict['data']:
                edge_dict['data'][prop_info['participant']].update(prop_info['data'])
            else:
                edge_dict['data'].update(prop_info['data'])

        return edge_dict


class Property(Base):
    """The property table contains additional information that is used to describe the context of a relation."""
    __tablename__ = PROPERTY_TABLE_NAME
    id = Column(Integer, primary_key=True)

    participant = Column(String(255))
    modifier = Column(String(255))
    relativeKey = Column(String(255), nullable=True)
    propValue = Column(String, nullable=True)
    namespaceEntry_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_ENTRY_TABLE_NAME)), nullable=True)
    namespaceEntry = relationship('NamespaceEntry')

    edges = relationship("Edge", secondary=edge_property)

    def forGraph(self):
        prop_dict = {
            'data': {
                self.participant: {
                    MODIFIER: self.modifier
                }
            },
            'participant': self.participant
        }
        if self.relativeKey:
            prop_dict['data'][EFFECT] = {
                self.relativeKey: self.propValue if self.propValue else self.namespaceEntry.forGraph()
            }

        return prop_dict


#class Node(Base):
#    """Represents a BEL Term"""
#    __tablename__ = NODE_TABLE_NAME
#
#    id = Column(Integer, primary_key=True)#
#
#    bel = Column(String, nullable=False)
#    blob = Column(Binary)


#class Edge(Base):
#    """Represents the relation between two BEL terms and its properties"""
#    __tablename__ = EDGE_TABLE_NAME

#    id = Column(Integer, primary_key=True)

#    source_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)))
#    source = relationship('Node', foreign_keys=[source_id])

#    target_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)))
#    target = relationship('Node', foreign_keys=[target_id])

#    evidence_id = Column(Integer, ForeignKey('{}.id'.format(EVIDENCE_TABLE_NAME)))
#    evidence = relationship("Evidence")

#    annotations = relationship('AnnotationEntry', secondary=edge_annotation)

#    relation = Column(String, nullable=False)
#    bel = Column(String, nullable=False)
#    blob = Column(Binary)


#class Evidence(Base):
#    """Represents a piece of support taken from a Publication"""
#    __tablename__ = EVIDENCE_TABLE_NAME
#    id = Column(Integer, primary_key=True)
#    text = Column(String, nullable=False, index=True)

#    citation_id = Column(Integer, ForeignKey('{}.id'.format(CITATION_TABLE_NAME)))
#    citation = relationship('Citation')


#class Citation(Base):
#    """The information about the citations that are used to prove a specific relation are stored in this table."""
#    __tablename__ = CITATION_TABLE_NAME

#    id = Column(Integer, primary_key=True)
#    type = Column(String(16), nullable=False)
#    name = Column(String(255), nullable=False)
#    reference = Column(String(255), nullable=False)
#    date = Column(Date, nullable=True)
#    comments = Column(String(255), nullable=True)

#    authors = relationship("Author", secondary=author_citation)
#
#    __table_args__ = (
#        UniqueConstraint(CITATION_TYPE, CITATION_REFERENCE),
#    )


#class Author(Base):
#    """Represents an Author of a publication"""
#    __tablename__ = AUTHOR_TABLE_NAME

#    id = Column(Integer, primary_key=True)
#    name = Column(String(255), nullable=False)

#    citations = relationship("Citation", secondary=author_citation)
