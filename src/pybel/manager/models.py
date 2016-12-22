from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Sequence, Text, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from ..parser.language import value_map

DEFINITION_TABLE_NAME = 'pybel_cache_definitions'
DEFINITION_ENTRY_TABLE_NAME = 'pybel_cache_entries'
DEFINITION_NAMESPACE = 'N'
DEFINITION_ANNOTATION = 'A'

OWL_TABLE_NAME = 'Owl'
OWL_ENTRY_TABLE_NAME = 'OwlEntry'

DEFAULT_BELNS_ENCODING = ''.join(sorted(value_map))

Base = declarative_base()


class Definition(Base):
    """This table represents the metadata for a BEL Namespace or annotation"""
    __tablename__ = DEFINITION_TABLE_NAME

    id = Column(Integer, primary_key=True)

    definitionType = Column(String(1))
    url = Column(String(255))
    author = Column(String(255))
    keyword = Column(String(50), index=True)
    createdDateTime = Column(DateTime)
    pubDate = Column(DateTime, nullable=True)
    copyright = Column(String(255))
    version = Column(String(50))
    contact = Column(String(255))

    entries = relationship('Entry', back_populates="definition")

    def __repr__(self):
        return '{}({})'.format('Namespace' if self.definitionType == 'N' else 'Annotation', self.keyword)


class Entry(Base):
    """This table represents the one-to-many relationship between a BEL Namespace/annotation,
        its values, and their semantic annotations"""
    __tablename__ = DEFINITION_ENTRY_TABLE_NAME

    id = Column(Integer, primary_key=True)

    name = Column(String(255), nullable=False)
    encoding = Column(String(len(value_map)), nullable=False, default=DEFAULT_BELNS_ENCODING)

    definition_id = Column(Integer, ForeignKey(DEFINITION_TABLE_NAME + '.id'), index=True)
    definition = relationship('Definition', back_populates='entries')

    def __repr__(self):
        return 'Entry(name={}, encoding={})'.format(self.name, self.encoding)


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
