from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Sequence, Text, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

DEFINITION_TABLE_NAME = 'pybel_cache_definition'
CONTEXT_TABLE_NAME = 'pybel_cache_context'
DEFINITION_NAMESPACE = 'N'
DEFINITION_ANNOTATION = 'A'

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
    contexts = relationship("Context", cascade='delete, delete-orphan')


class Context(Base):
    """This table represents the one-to-many relationship between a BEL Namespace/annotation, its values, and their semantic annotations"""
    __tablename__ = CONTEXT_TABLE_NAME

    id = Column(Integer, primary_key=True)
    definition_id = Column(Integer, ForeignKey('pybel_cache_definition.id'), index=True)
    context = Column(String(255))
    encoding = Column(String(50))


owl_relationship = Table(
    'owl_relationship', Base.metadata,
    Column('left_id', Integer, ForeignKey('OwlEntry.id'), primary_key=True),
    Column('right_id', Integer, ForeignKey('OwlEntry.id'), primary_key=True)
)


class Owl(Base):
    __tablename__ = 'Owl'

    id = Column(Integer, Sequence('owl_id_seq'), primary_key=True)
    iri = Column(Text, unique=True)
    entries = relationship("OwlEntry", order_by="OwlEntry.id", backref="owl")

    def __repr__(self):
        return "Owl(iri='{}', #entries='{}')>".format(self.iri, list(self.entries))


class OwlEntry(Base):
    __tablename__ = 'OwlEntry'

    id = Column(Integer, Sequence('OwlEntry_id_seq'), primary_key=True)
    owl_id = Column(Integer, ForeignKey('Owl.id'), index=True)
    entry = Column(String(255))
    encoding = Column(String(50))

    children = relationship('OwlEntry',
                            secondary=owl_relationship,
                            primaryjoin=id == owl_relationship.c.left_id,
                            secondaryjoin=id == owl_relationship.c.right_id)

    def __repr__(self):
        return 'OwlEntry({})'.format(self.entry)