from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

NAMESPACE_TABLE_NAME = 'pybel_cache_namespace'
NAMESPACENAME_TABLE_NAME = 'pybel_cache_name'

Base = declarative_base()


class Namespace(Base):
    __tablename__ = NAMESPACE_TABLE_NAME

    id = Column(Integer, primary_key=True)
    url = Column(String(255))
    author = Column(String(255))
    keyword = Column(String(50), index=True)
    createdDateTime = Column(DateTime)
    pubDate = Column(DateTime, nullable=True)
    copyright = Column(String(255))
    version = Column(String(50))
    contact = Column(String(255))
    names = relationship("NamespaceName", cascade='delete, delete-orphan')


class NamespaceName(Base):
    __tablename__ = NAMESPACENAME_TABLE_NAME

    id = Column(Integer, primary_key=True)
    namespace_id = Column(Integer, ForeignKey('pybel_cache_namespace.id'), index=True)
    name = Column(String(255))
    encoding = Column(String(50))
