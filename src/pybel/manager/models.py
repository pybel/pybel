from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Sequence, Text, Table, Enum, Date
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

OWL_TABLE_NAME = 'Owl'
OWL_ENTRY_TABLE_NAME = 'OwlEntry'

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
    #domain = Column(Enum(*NAMESPACE_DOMAIN_TYPES, name='namespaceDomain_types'))
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
    'owl_relationship', Base.metadata,
    Column('left_id', Integer, ForeignKey('OwlEntry.id'), primary_key=True),
    Column('right_id', Integer, ForeignKey('OwlEntry.id'), primary_key=True)
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
