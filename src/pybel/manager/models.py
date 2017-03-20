# -*- coding: utf-8 -*-

"""This module contains the database models that support the PyBEL definition cache and graph cache"""

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

    url = Column(String(255), doc='Source url of the given namespace definition file (.belns)')
    keyword = Column(String(8), index=True, doc='Keyword that is used in a BEL file to identify a specific namespace')
    name = Column(String(255))
    domain = Column(String(255))
    species = Column(String(255), nullable=True,
                     doc='NCBI identifier that states for what species the namespace is valid')
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

    name = Column(String(255), nullable=False,
                  doc='Name that is defined in the corresponding namespace definition file')
    encoding = Column(String(8), nullable=True,
                      doc='Represents the biological entities that this name is valid for (e.g. G for Gene or P for Protein)')

    namespace_id = Column(Integer, ForeignKey(NAMESPACE_TABLE_NAME + '.id'), index=True)
    namespace = relationship('Namespace', back_populates='entries')

    equivalence_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_EQUIVALENCE_CLASS_TABLE_NAME)), nullable=True)
    equivalence = relationship('NamespaceEntryEquivalence', back_populates='members')

    @property
    def data(self):
        return {
            NAMESPACE: self.namespace.keyword,
            NAME: self.name
        }


class NamespaceEntryEquivalence(Base):
    __tablename__ = NAMESPACE_EQUIVALENCE_CLASS_TABLE_NAME

    id = Column(Integer, primary_key=True)
    label = Column(String(255), nullable=False, unique=True, index=True)

    members = relationship('NamespaceEntry', back_populates='equivalence')


class Annotation(Base):
    """Represents a BEL Annotation"""
    __tablename__ = ANNOTATION_TABLE_NAME

    id = Column(Integer, primary_key=True)

    url = Column(String(255), doc='Source url of the given annotation definition file (.belanno)')
    keyword = Column(String(50), index=True, doc='Keyword that is used in a BEL file to identify a specific annotation')
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

    name = Column(String(255), nullable=False,
                  doc='Name that is defined in the corresponding annotation definition file')
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

edge_annotation = Table(
    EDGE_ANNOTATION_TABLE_NAME, Base.metadata,
    Column('edge_id', Integer, ForeignKey('{}.id'.format(EDGE_TABLE_NAME)), primary_key=True),
    Column('annotationEntry_id', Integer, ForeignKey('{}.id'.format(ANNOTATION_ENTRY_TABLE_NAME)), primary_key=True)
)


class Network(Base):
    """Represents a collection of edges, specified by a BEL Script"""
    __tablename__ = NETWORK_TABLE_NAME

    id = Column(Integer, primary_key=True)

    name = Column(String(255), index=True, doc='Name of the given Network (from the BEL file)')
    version = Column(String(255), doc='Release version of the given Network (from the BEL file)')

    authors = Column(Text, nullable=True, doc='Authors of the underlying BEL file')
    contact = Column(String(255), nullable=True, doc='Contact information extracted from the underlying BEL file')
    description = Column(Text, nullable=True, doc='Descriptive text extracted from the BEL file')
    copyright = Column(String(255), nullable=True, doc='Copyright information')
    disclaimer = Column(String(255), nullable=True)
    licenses = Column(String(255), nullable=True, doc='License information')

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

    type = Column(String(255), nullable=False, doc='The type of the represented biological entity e.g. Protein or Gene')
    namespaceEntry_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_ENTRY_TABLE_NAME)), nullable=True)
    namespaceEntry = relationship('NamespaceEntry', foreign_keys=[namespaceEntry_id])
    namespacePattern = Column(String(255), nullable=True, doc="Contains regex pattern for value identification.")
    is_variant = Column(Boolean, default=False, doc='Identifies weather or not the given node is a variant')
    fusion = Column(Boolean, default=False, doc='Identifies weather or not the given node is a fusion')

    bel = Column(String, nullable=False, doc='Valid BEL term that represents the given node')
    blob = Column(Binary)

    modifications = relationship("Modification", secondary=node_modification)

    @property
    def data(self):
        node_key = [self.type]
        node_data = {
            FUNCTION: self.type,
        }
        if self.namespaceEntry:
            namespace_entry = self.namespaceEntry.data
            node_data.update(namespace_entry)
            node_key.append(namespace_entry[NAMESPACE])
            node_key.append(namespace_entry[NAME])

        elif self.is_variant:
            if self.fusion:
                mod = self.modifications[0].data
                node_data[FUSION] = mod['mod_data']
                [node_key.append(key_element) for key_element in mod['mod_key']]
            else:
                node_data[VARIANTS] = []
                for modification in self.modifications:
                    mod = modification.data
                    node_data[VARIANTS].append(mod['mod_data'])
                    node_key.append(tuple(mod['mod_key']))

        return {'key': tuple(node_key), 'data': node_data}


class Modification(Base):
    """The modifications that are present in the network are stored in this table."""
    __tablename__ = MODIFICATION_TABLE_NAME

    id = Column(Integer, primary_key=True)

    modType = Column(String(255), doc='Type of the stored modification e.g. Fusion')
    variantString = Column(String, nullable=True)

    p3PartnerName_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_ENTRY_TABLE_NAME)), nullable=True)
    p3Partner = relationship("NamespaceEntry", foreign_keys=[p3PartnerName_id])

    p3Reference = Column(String(10), nullable=True)
    p3Start = Column(String(255), nullable=True)
    p3Stop = Column(String(255), nullable=True)
    p3Missing = Column(String(10), nullable=True)

    p5PartnerName_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_ENTRY_TABLE_NAME)), nullable=True)
    p5Partner = relationship("NamespaceEntry", foreign_keys=[p5PartnerName_id])

    p5Reference = Column(String(10), nullable=True)
    p5Start = Column(String(255), nullable=True)
    p5Stop = Column(String(255), nullable=True)
    p5Missing = Column(String(10), nullable=True)

    modNamespace = Column(String(255), nullable=True, doc='Namespace for the modification name')
    modName = Column(String(255), nullable=True, doc='Name of the given modification (used for pmod or gmod)')
    aminoA = Column(String(3), nullable=True, doc='Three letter amino accid code')
    position = Column(Integer, nullable=True, doc='Position')

    nodes = relationship("Node", secondary=node_modification)

    @property
    def data(self):
        """Recreates a is_variant dictionary for PyBEL.BELGraph.

        :return: Dictionary that describes a variant or a fusion.
        :rtype: dict
        """
        mod_dict = {}
        mod_key = []
        if self.modType == FUSION:
            mod_dict.update({
                PARTNER_3P: self.p3Partner.data,
                PARTNER_5P: self.p5Partner.data,
                RANGE_3P: {},
                RANGE_5P: {}
            })

            mod_key.append((mod_dict[PARTNER_5P][NAMESPACE], mod_dict[PARTNER_5P][NAME],))

            if self.p5Missing:
                mod_dict[RANGE_5P] = {FUSION_MISSING: self.p5Missing}
                mod_key.append((self.p5Missing,))

            else:
                mod_dict[RANGE_5P].update({
                    FUSION_REFERENCE: self.p5Reference,
                    FUSION_START: self.p5Start,
                    FUSION_STOP: self.p5Stop
                })
                mod_key.append((self.p5Reference, self.p5Start, self.p5Stop,))

            mod_key.append((mod_dict[PARTNER_3P][NAMESPACE], mod_dict[PARTNER_3P][NAME],))

            if self.p3Missing:
                mod_dict[RANGE_3P][FUSION_MISSING] = self.p3Missing
                mod_key.append((self.p3Missing,))

            else:
                mod_dict[RANGE_3P].update({
                    FUSION_REFERENCE: self.p3Reference,
                    FUSION_START: self.p3Start,
                    FUSION_STOP: self.p3Stop
                })
                mod_key.append((self.p3Reference, self.p3Start, self.p3Stop,))


        else:
            mod_dict[KIND] = self.modType
            mod_key.append(self.modType)
            if self.modType == HGVS:
                mod_dict[IDENTIFIER] = self.variantString

            elif self.modType == FRAGMENT:
                if self.p3Missing:
                    mod_dict[FRAGMENT_MISSING] = self.p3Missing
                    mod_key.append(self.p3Missing)
                else:
                    mod_dict.update({
                        FRAGMENT_START: self.p3Start,
                        FRAGMENT_STOP: self.p3Stop
                    })
                    mod_key.append((self.p3Start, self.p3Stop,))

            elif self.modType == GMOD:
                mod_dict.update({
                    IDENTIFIER: {
                        NAMESPACE: self.modNamespace,
                        NAME: self.modName
                    }
                })
                mod_key.append((self.modNamespace, self.modName,))

            elif self.modType == PMOD:
                mod_dict.update({
                    IDENTIFIER: {
                        NAMESPACE: self.modNamespace,
                        NAME: self.modName
                    }
                })
                mod_key.append((self.modNamespace, self.modName,))
                if self.aminoA:
                    mod_dict[PMOD_CODE] = self.aminoA
                    mod_key.append(self.aminoA)

                if self.position:
                    mod_dict[PMOD_POSITION] = self.position
                    mod_key.append(self.position)

        return {
            'mod_data': mod_dict,
            'mod_key': mod_key
        }


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
    type = Column(String(16), nullable=False, doc='Type of the stored publication e.g. PubMed')
    name = Column(String(255), nullable=False, doc='Title of the publication')
    reference = Column(String(255), nullable=False, doc='Reference identifier of the publication e.g. PubMed_ID')
    date = Column(Date, nullable=True, doc='Publication date')

    authors = relationship("Author", secondary=author_citation)
    evidences = relationship("Evidence", back_populates='citation')

    __table_args__ = (
        UniqueConstraint(CITATION_TYPE, CITATION_REFERENCE),
    )

    @property
    def data(self):
        """Creates a citation dictionary that is used to recreate the edge data dictionary of a PyBEL.BELGraph.

        :return: Citation dictionary for the recreation of a PyBEL.BELGraph.
        :rtype: dict
        """
        citation_dict = {
            CITATION_NAME: self.name,
            CITATION_REFERENCE: self.reference,
            CITATION_TYPE: self.type
        }
        if self.authors:
            citation_dict[CITATION_AUTHORS] = "|".join(author.name for author in self.authors)
        if self.date:
            citation_dict[CITATION_DATE] = self.date.strftime('%Y-%m-%d')

        return citation_dict


class Evidence(Base):
    """This table contains the evidence text that proves a specific relationship and refers the source that is cited."""
    __tablename__ = EVIDENCE_TABLE_NAME

    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False, index=True, doc='Supporting text that is cited from a given publication')

    citation_id = Column(Integer, ForeignKey('{}.id'.format(CITATION_TABLE_NAME)))
    citation = relationship('Citation', back_populates='evidences')

    @property
    def data(self):
        """Creates a dictionary that is used to recreate the edge data dictionary for a PyBEL.BELGraph.

        :return: Dictionary containing citation and evidence for a PyBEL.BELGraph edge.
        :rtype: dict
        """
        return {
            CITATION: self.citation.data,
            EVIDENCE: self.text
        }


edge_property = Table(
    EDGE_PROPERTY_TABLE_NAME, Base.metadata,
    Column('edge_id', Integer, ForeignKey('{}.id'.format(EDGE_TABLE_NAME))),
    Column('property_id', Integer, ForeignKey('{}.id'.format(PROPERTY_TABLE_NAME)))
)


class Edge(Base):
    """Relationships are represented in this table. It shows the nodes that are in a relation to eachother and provides
    information about the context of the relation by refaring to the annotation, property and evidence tables.
    """
    __tablename__ = EDGE_TABLE_NAME

    id = Column(Integer, primary_key=True)

    graphIdentifier = Column(Integer,
                             doc='Identifier that is used in the PyBEL.BELGraph to identify weather or not an edge is artificial')
    bel = Column(String, nullable=False, doc='Valid BEL statement that represents the given edge')
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

    @property
    def data(self):
        """Creates a dictionary of one BEL Edge that can be used to create an edge in a PyBEL.BELGraph.

        :return: Dictionary that contains information about an edge of a PyBEL.BELGraph. Including participants
                 and edge data informations.
        :rtype: dict
        """
        source_node = self.source.data
        target_node = self.target.data
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
        edge_dict['data'].update(self.evidence.data)
        edge_dict['data'][ANNOTATIONS] = {}
        if self.annotations:
            for anno in self.annotations:
                edge_dict['data'][ANNOTATIONS][anno.annotation.keyword] = anno.name
        for prop in self.properties:
            prop_info = prop.data
            if prop_info['participant'] in edge_dict['data']:
                edge_dict['data'][prop_info['participant']].update(prop_info['data'])
            else:
                edge_dict['data'].update(prop_info['data'])

        return edge_dict


class Property(Base):
    """The property table contains additional information that is used to describe the context of a relation."""
    __tablename__ = PROPERTY_TABLE_NAME

    id = Column(Integer, primary_key=True)

    participant = Column(String(255), doc='Identifies which participant of the edge if affected by the given property')
    modifier = Column(String(255), doc='The modifier to the corresponding participant')
    relativeKey = Column(String(255), nullable=True, doc='Relative key of effect e.g. to_tloc or from_tloc')
    propValue = Column(String, nullable=True, doc='Value of the effect')
    namespaceEntry_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_ENTRY_TABLE_NAME)), nullable=True)
    namespaceEntry = relationship('NamespaceEntry')

    edges = relationship("Edge", secondary=edge_property)

    @property
    def data(self):
        """Creates a property dict that is used to recreate an edge dictionary for PyBEL.BELGraph.

        :return: Property dictionary of an edge that is participant (sub/obj) related.
        :rtype: dict
        """
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
                self.relativeKey: self.propValue if self.propValue else self.namespaceEntry.data
            }

        return prop_dict
