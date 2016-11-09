from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
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
