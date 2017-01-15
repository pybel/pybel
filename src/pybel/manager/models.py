import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Sequence, Text, Table, Date, Binary, \
    UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

DEFINITION_TABLE_NAME = 'pybel_cache_definitions'
DEFINITION_ENTRY_TABLE_NAME = 'pybel_cache_entries'
DEFINITION_NAMESPACE = 'N'
DEFINITION_ANNOTATION = 'A'

NAMESPACE_TABLE_NAME = 'pybel_namespaces'
NAMESPACE_ENTRY_TABLE_NAME = 'pybel_namespaceEntries'
ANNOTATION_TABLE_NAME = 'pybel_annotations'
ANNOTATION_ENTRY_TABLE_NAME = 'pybel_annotationEntries'

NETWORK_TABLE_NAME = 'pybel_network'
CITATION_TABLE_NAME = 'pybel_citation'
EVIDENCE_TABLE_NAME = 'pybel_evidence'
EDGE_TABLE_NAME = 'pybel_edge'
NODE_TABLE_NAME = 'pybel_node'
EDGE_ANNOTATION_TABLE_NAME = 'pybel_edge_annotationEntries'
NETWORK_EDGE_TABLE_NAME = 'pybel_network_edge'

OWL_TABLE_NAME = 'Owl'
OWL_ENTRY_TABLE_NAME = 'OwlEntry'
OWL_RELATIONSHIP_TABLE_NAME = 'OwlRelationship'

Base = declarative_base()

NAMESPACE_DOMAIN_TYPES = {"BiologicalProcess", "Chemical", "Gene and Gene Products", "Other"}
"""See: https://wiki.openbel.org/display/BELNA/Custom+Namespaces"""

CITATION_TYPES = {"Book", "PubMed", "Journal", "Online Resource", "Other"}
"""See: https://wiki.openbel.org/display/BELNA/Citation"""


class Namespace(Base):
    __tablename__ = NAMESPACE_TABLE_NAME
    id = Column(Integer, primary_key=True)

    url = Column(String(255))
    keyword = Column(String(8), index=True)
    name = Column(String(255))
    domain = Column(String(255))
    # domain = Column(Enum(*NAMESPACE_DOMAIN_TYPES, name='namespaceDomain_types'))
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

    def __repr__(self):
        return 'Namespace({})'.format(self.keyword)


class NamespaceEntry(Base):
    __tablename__ = NAMESPACE_ENTRY_TABLE_NAME
    id = Column(Integer, primary_key=True)

    name = Column(String(255), nullable=False)
    encoding = Column(String(8), nullable=True)

    namespace_id = Column(Integer, ForeignKey(NAMESPACE_TABLE_NAME + '.id'), index=True)
    namespace = relationship('Namespace', back_populates='entries')

    def __repr__(self):
        return 'NamespaceEntry({}, {})'.format(self.name, self.encoding)


class Annotation(Base):
    """This table represents the metadata for a BEL Namespace or annotation"""
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

    def __repr__(self):
        return 'Annotation({})'.format(self.keyword)


class AnnotationEntry(Base):
    __tablename__ = ANNOTATION_ENTRY_TABLE_NAME
    id = Column(Integer, primary_key=True)

    name = Column(String(255), nullable=False)
    label = Column(String(255), nullable=True)

    annotation_id = Column(Integer, ForeignKey(ANNOTATION_TABLE_NAME + '.id'), index=True)
    annotation = relationship('Annotation', back_populates='entries')

    def __repr__(self):
        return 'AnnotationEntry({}, {})'.format(self.name, self.label)


owl_relationship = Table(
    OWL_RELATIONSHIP_TABLE_NAME, Base.metadata,
    Column('left_id', Integer, ForeignKey('{}.id'.format(OWL_ENTRY_TABLE_NAME)), primary_key=True),
    Column('right_id', Integer, ForeignKey('{}.id'.format(OWL_ENTRY_TABLE_NAME)), primary_key=True)
)


class Owl(Base):
    __tablename__ = OWL_TABLE_NAME

    id = Column(Integer, Sequence('Owl_id_seq'), primary_key=True)
    iri = Column(Text, unique=True)

    entries = relationship("OwlEntry", back_populates='owl')

    def __repr__(self):
        return "Owl(iri={})>".format(self.iri)


class OwlEntry(Base):
    __tablename__ = OWL_ENTRY_TABLE_NAME

    id = Column(Integer, Sequence('OwlEntry_id_seq'), primary_key=True)

    entry = Column(String(255))
    encoding = Column(String(50))

    owl_id = Column(Integer, ForeignKey('Owl.id'), index=True)
    owl = relationship('Owl', back_populates='entries')

    children = relationship('OwlEntry',
                            secondary=owl_relationship,
                            primaryjoin=id == owl_relationship.c.left_id,
                            secondaryjoin=id == owl_relationship.c.right_id)

    def __repr__(self):
        return 'OwlEntry({}:{})'.format(self.owl, self.entry)


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
        UniqueConstraint("name", "version"),
    )


class Node(Base):
    __tablename__ = NODE_TABLE_NAME
    id = Column(Integer, primary_key=True)
    bel = Column(String, nullable=False)

    def __repr__(self):
        return self.bel


class Citation(Base):
    __tablename__ = CITATION_TABLE_NAME
    id = Column(Integer, primary_key=True)
    type = Column(String(16), nullable=False)
    name = Column(String, nullable=False)
    reference = Column(String, nullable=False)
    date = Column(Date, nullable=True)
    authors = Column(String, nullable=True)
    comments = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("type", "reference"),
    )


class Evidence(Base):
    __tablename__ = EVIDENCE_TABLE_NAME
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False, index=True)

    citation_id = Column(Integer, ForeignKey('{}.id'.format(CITATION_TABLE_NAME)))
    citation = relationship('Citation')


class Edge(Base):
    __tablename__ = EDGE_TABLE_NAME
    id = Column(Integer, primary_key=True)
    bel = Column(String, nullable=False)
    relation = Column(String, nullable=False)

    source_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)))
    source = relationship('Node', foreign_keys=[source_id])

    target_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)))
    target = relationship('Node', foreign_keys=[target_id])

    evidence_id = Column(Integer, ForeignKey('{}.id'.format(EVIDENCE_TABLE_NAME)))
    evidence = relationship("Evidence")

    annotations = relationship('AnnotationEntry', secondary=edge_annotation)

    def __repr__(self):
        return self.bel
