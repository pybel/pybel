# -*- coding: utf-8 -*-

"""This module contains the SQLAlchemy database models that support the definition cache and graph cache."""

import datetime
from collections import defaultdict
from typing import Any, Iterable, Mapping, Optional, Tuple

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, JSON, LargeBinary, String, Table, Text, UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship

from .. import constants as pc
from ..constants import (
    CITATION, CITATION_AUTHORS, CITATION_DATE, CITATION_FIRST_AUTHOR, CITATION_JOURNAL, CITATION_LAST_AUTHOR, CITATION_PAGES, CITATION_VOLUME, EVIDENCE, IDENTIFIER, METADATA_AUTHORS, METADATA_CONTACT, METADATA_COPYRIGHT, METADATA_DESCRIPTION, METADATA_DISCLAIMER, METADATA_LICENSES, METADATA_NAME, METADATA_VERSION, NAME, NAMESPACE,
)
from ..io.gpickle import from_bytes_gz, to_bytes_gz
from ..language import CitationDict, Entity
from ..struct.graph import BELGraph
from ..tokens import parse_result_to_dsl

__all__ = [
    'Base',
    'Namespace',
    'NamespaceEntry',
    'Network',
    'Node',
    'Author',
    'Citation',
    'Evidence',
    'Edge',
    'edge_annotation',
    'network_edge',
    'network_node',
]

NAME_TABLE_NAME = 'pybel_name'
NAMESPACE_TABLE_NAME = 'pybel_namespace'

NODE_TABLE_NAME = 'pybel_node'

EDGE_TABLE_NAME = 'pybel_edge'
EDGE_ANNOTATION_TABLE_NAME = 'pybel_edge_name'

AUTHOR_TABLE_NAME = 'pybel_author'
CITATION_TABLE_NAME = 'pybel_citation'
AUTHOR_CITATION_TABLE_NAME = 'pybel_author_citation'

EVIDENCE_TABLE_NAME = 'pybel_evidence'

NETWORK_TABLE_NAME = 'pybel_network'
NETWORK_NODE_TABLE_NAME = 'pybel_network_node'
NETWORK_EDGE_TABLE_NAME = 'pybel_network_edge'
NETWORK_NAMESPACE_TABLE_NAME = 'pybel_network_namespace'
NETWORK_ANNOTATION_TABLE_NAME = 'pybel_network_annotation'

LONGBLOB = 4294967295

Base = declarative_base()


class Namespace(Base):
    """Represents a BEL Namespace."""

    __tablename__ = NAMESPACE_TABLE_NAME

    id = Column(Integer, primary_key=True)
    uploaded = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, doc='The date of upload')

    # logically the "namespace"
    keyword = Column(
        String(255), nullable=True, index=True,
        doc='Keyword that is used in a BEL file to identify a specific namespace',
    )

    # A namespace either needs a URL or a pattern
    pattern = Column(
        String(255), nullable=True, index=True,
        doc="Contains regex pattern for value identification.",
    )

    miriam_id = Column(
        String(16), nullable=True,
        doc=r'MIRIAM resource identifier matching the regular expression ``^MIR:001\d{5}$``',
    )
    miriam_name = Column(String(255), nullable=True)
    miriam_namespace = Column(String(255), nullable=True)
    miriam_uri = Column(String(255), nullable=True)
    miriam_description = Column(Text, nullable=True)

    version = Column(String(255), nullable=True, doc='Version of the namespace')

    url = Column(String(255), nullable=True, unique=True, index=True, doc='BELNS Resource location as URL')

    name = Column(String(255), nullable=True, doc='Name of the given namespace')
    domain = Column(String(255), nullable=True, doc='Domain for which this namespace is valid')
    species = Column(String(255), nullable=True, doc='Taxonomy identifiers for which this namespace is valid')
    description = Column(Text, nullable=True, doc='Optional short description of the namespace')

    created = Column(DateTime, nullable=True, doc='DateTime of the creation of the namespace definition file')
    query_url = Column(Text, nullable=True, doc='URL that can be used to query the namespace (externally from PyBEL)')

    author = Column(String(255), nullable=True, doc='The author of the namespace')
    license = Column(String(255), nullable=True, doc='License information')
    contact = Column(String(255), nullable=True, doc='Contact information')

    citation = Column(String(255), nullable=True)
    citation_description = Column(Text, nullable=True)
    citation_version = Column(String(255), nullable=True)
    citation_published = Column(Date, nullable=True)
    citation_url = Column(String(255), nullable=True)

    is_annotation = Column(Boolean)

    def __str__(self):
        return f'[id={self.id}] {self.keyword}'

    def get_term_to_encodings(self) -> Mapping[Tuple[Optional[str], str], str]:
        """Return the term (db, id, name) to encodings from this namespace."""
        return {
            (entry.identifier, entry.name): entry.encoding
            for entry in self.entries
        }

    def to_json(self, include_id: bool = False) -> Mapping[str, str]:
        """Return the most useful entries as a dictionary.

        :param include_id: If true, includes the model identifier
        """
        result = {
            'keyword': self.keyword,
            'name': self.name,
            'version': self.version,
        }

        if self.url:
            result['url'] = self.url
        else:
            result['pattern'] = self.pattern

        if include_id:
            result['id'] = self.id

        return result


class NamespaceEntry(Base):
    """Represents a name within a BEL namespace."""

    __tablename__ = NAME_TABLE_NAME
    id = Column(Integer, primary_key=True)

    name = Column(
        String(1023), index=True, nullable=True,
        doc='Name that is defined in the corresponding namespace definition file',
    )
    identifier = Column(String(255), index=True, nullable=True, doc='The database accession number')
    encoding = Column(String(8), nullable=True, doc='The biological entity types for which this name is valid')

    namespace_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_TABLE_NAME)), nullable=False, index=True)
    namespace = relationship(Namespace, backref=backref('entries', lazy='dynamic'))

    is_name = Column(Boolean)
    is_annotation = Column(Boolean)

    def to_json(self, include_id: bool = False) -> Mapping[str, str]:
        """Describe the namespaceEntry as dictionary of Namespace-Keyword and Name.

        :param include_id: If true, includes the model identifier
        """
        result = {
            NAMESPACE: self.namespace.keyword,
        }

        if self.name:
            result[NAME] = self.name

        if self.identifier:
            result[IDENTIFIER] = self.identifier

        if include_id:
            result['id'] = self.id

        return result

    @classmethod
    def name_contains(cls, name_query: str):
        """Make a filter if the name contains a certain substring."""
        return cls.name.contains(name_query)

    def __str__(self):
        return '[id={namespace_id}] {namespace_name}:{identifier} ! {name}'.format(
            namespace_id=self.namespace.id,
            namespace_name=self.namespace.keyword,
            identifier=self.identifier,
            name=self.name,
        )


network_edge = Table(
    NETWORK_EDGE_TABLE_NAME, Base.metadata,
    Column('network_id', Integer, ForeignKey('{}.id'.format(NETWORK_TABLE_NAME)), primary_key=True),
    Column('edge_id', Integer, ForeignKey('{}.id'.format(EDGE_TABLE_NAME)), primary_key=True),
)

network_node = Table(
    NETWORK_NODE_TABLE_NAME, Base.metadata,
    Column('network_id', Integer, ForeignKey('{}.id'.format(NETWORK_TABLE_NAME)), primary_key=True),
    Column('node_id', Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)), primary_key=True),
)


class Network(Base):
    """Represents a collection of edges, specified by a BEL Script."""

    __tablename__ = NETWORK_TABLE_NAME
    id = Column(Integer, primary_key=True)

    name = Column(String(255), nullable=False, index=True, doc='Name of the given Network (from the BEL file)')
    version = Column(String(255), nullable=False, doc='Release version of the given Network (from the BEL file)')

    authors = Column(Text, nullable=True, doc='Authors of the underlying BEL file')
    contact = Column(String(255), nullable=True, doc='Contact email from the underlying BEL file')
    description = Column(Text, nullable=True, doc='Descriptive text from the underlying BEL file')
    copyright = Column(Text, nullable=True, doc='Copyright information')
    disclaimer = Column(Text, nullable=True, doc='Disclaimer information')
    licenses = Column(Text, nullable=True, doc='License information')

    created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    blob = Column(LargeBinary(LONGBLOB), doc='A pickled version of this network')

    nodes = relationship('Node', secondary=network_node, lazy='dynamic', backref=backref('networks', lazy='dynamic'))
    edges = relationship('Edge', secondary=network_edge, lazy='dynamic', backref=backref('networks', lazy='dynamic'))

    def to_json(self, include_id: bool = False) -> Mapping[str, Any]:
        """Return this network as JSON.

        :param include_id: If true, includes the model identifier
        """
        result = {
            METADATA_NAME: self.name,
            METADATA_VERSION: self.version,
        }

        if self.created:
            result['created'] = str(self.created)

        if include_id:
            result['id'] = self.id

        if self.authors:
            result[METADATA_AUTHORS] = self.authors

        if self.contact:
            result[METADATA_CONTACT] = self.contact

        if self.description:
            result[METADATA_DESCRIPTION] = self.description

        if self.copyright:
            result[METADATA_COPYRIGHT] = self.copyright

        if self.disclaimer:
            result[METADATA_DISCLAIMER] = self.disclaimer

        if self.licenses:
            result[METADATA_LICENSES] = self.licenses

        return result

    @classmethod
    def name_contains(cls, name_query: str):
        """Build a filter for networks whose names contain the query."""
        return cls.name.contains(name_query)

    @classmethod
    def description_contains(cls, description_query: str):
        """Build a filter for networks whose descriptions contain the query."""
        return cls.description.contains(description_query)

    @classmethod
    def id_in(cls, network_ids: Iterable[int]):
        """Build a filter for networks whose identifiers appear in the given sequence."""
        return cls.id.in_(network_ids)

    def __repr__(self):
        return '{} v{}'.format(self.name, self.version)

    def __str__(self):
        return repr(self)

    def as_bel(self) -> BELGraph:
        """Get this network and loads it into a :class:`BELGraph`."""
        return from_bytes_gz(self.blob)

    def store_bel(self, graph: BELGraph):
        """Insert a BEL graph."""
        self.blob = to_bytes_gz(graph)


class Node(Base):
    """Represents a BEL Term."""

    __tablename__ = NODE_TABLE_NAME
    id = Column(Integer, primary_key=True)

    type = Column(String(32), nullable=False, doc='The type of the represented biological entity e.g. Protein or Gene')
    bel = Column(String(1023), nullable=False, doc='Canonical BEL term that represents the given node')
    md5 = Column(String(255), nullable=False, unique=True, index=True)

    namespace_entry_id = Column(Integer, ForeignKey('{}.id'.format(NAME_TABLE_NAME)), nullable=True)
    namespace_entry = relationship(NamespaceEntry, foreign_keys=[namespace_entry_id],
                                   backref=backref('nodes', lazy='dynamic'))

    data = Column(JSON, nullable=False, doc='PyBEL BaseEntity as JSON')

    @staticmethod
    def _start_from_base_entity(base_entity) -> 'Node':
        """Convert a base entity to a node model.

        :type base_entity: pybel.dsl.BaseEntity
        """
        return Node(
            type=base_entity.function,
            bel=base_entity.as_bel(),
            md5=base_entity.md5,
            data=base_entity,
        )

    @classmethod
    def bel_contains(cls, bel_query: str):
        """Build a filter for nodes whose BEL contain the query."""
        return cls.bel.contains(bel_query)

    def __str__(self):
        return self.bel

    def __repr__(self):
        return '<Node {}: {}>'.format(self.md5[:10], self.bel)

    def _get_list_by_relation(self, relation):
        return [
            edge.target.to_json()
            for edge in self.out_edges.filter(Edge.relation == relation)
        ]

    def as_bel(self):
        """Serialize this node as a PyBEL DSL object.

        :rtype: pybel.dsl.BaseEntity
        """
        return parse_result_to_dsl(self.data)

    def to_json(self):
        """Serialize this node as a JSON object using as_bel()."""
        return self.as_bel()


author_citation = Table(
    AUTHOR_CITATION_TABLE_NAME, Base.metadata,
    Column('author_id', Integer, ForeignKey('{}.id'.format(AUTHOR_TABLE_NAME)), primary_key=True),
    Column('citation_id', Integer, ForeignKey('{}.id'.format(CITATION_TABLE_NAME)), primary_key=True),
)


class Author(Base):
    """Contains all author names."""

    __tablename__ = AUTHOR_TABLE_NAME

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True, index=True)

    @classmethod
    def name_contains(cls, name_query: str):
        """Build a filter for authors whose names contain the given query."""
        return cls.name.contains(name_query)

    @classmethod
    def has_name_in(cls, names: Iterable[str]):
        """Build a filter if the author has any of the given names."""
        return cls.name.in_(names)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'Author(name="{self.name}")'


class Citation(Base):
    """The information about the citations that are used to prove a specific relation are stored in this table."""

    __tablename__ = CITATION_TABLE_NAME

    id = Column(Integer, primary_key=True)

    db = Column(String(16), nullable=False, doc='Type of the stored publication e.g. PubMed')
    db_id = Column(String(255), nullable=False, doc='Reference identifier of the publication e.g. PubMed_ID')

    article_type = Column(Text, nullable=True, doc='Type of the publication')
    title = Column(Text, nullable=True, doc='Title of the publication')
    journal = Column(Text, nullable=True, doc='Journal name')
    volume = Column(Text, nullable=True, doc='Volume of the journal')
    issue = Column(Text, nullable=True, doc='Issue within the volume')
    pages = Column(Text, nullable=True, doc='Pages of the publication')
    date = Column(Date, nullable=True, doc='Publication date')

    first_id = Column(Integer, ForeignKey('{}.id'.format(AUTHOR_TABLE_NAME)), nullable=True, doc='First author')
    first = relationship(Author, foreign_keys=[first_id])

    last_id = Column(Integer, ForeignKey('{}.id'.format(AUTHOR_TABLE_NAME)), nullable=True, doc='Last author')
    last = relationship(Author, foreign_keys=[last_id])

    authors = relationship(Author, secondary=author_citation, backref='citations')

    __table_args__ = (
        UniqueConstraint(db, db_id),
    )

    def __str__(self):
        return '{}:{}'.format(self.db, self.db_id)

    @property
    def is_pubmed(self) -> bool:
        """Return if this is a PubMed citation."""
        return self.db == 'pubmed'

    @property
    def is_enriched(self) -> bool:
        """Return if this citation has been enriched for name, title, and other metadata."""
        return all(f is not None for f in (self.title, self.journal))

    def to_json(self, include_id: bool = False) -> Mapping[str, Any]:
        """Create a citation dictionary that is used to recreate the edge data dictionary of a :class:`BELGraph`.

        :param bool include_id: If true, includes the model identifier
        :return: Citation dictionary for the recreation of a :class:`BELGraph`.
        """
        result = CitationDict(
            namespace=self.db,
            identifier=self.db_id,
            name=self.title,
        )

        if include_id:
            result['id'] = self.id

        if self.title:
            result[NAME] = self.title

        if self.journal:
            result[CITATION_JOURNAL] = self.journal

        if self.volume:
            result[CITATION_VOLUME] = self.volume

        if self.pages:
            result[CITATION_PAGES] = self.pages

        if self.date:
            result[CITATION_DATE] = self.date.strftime('%Y-%m-%d')

        if self.first:
            result[CITATION_FIRST_AUTHOR] = self.first.name

        if self.last:
            result[CITATION_LAST_AUTHOR] = self.last.name

        if self.article_type:
            result[pc.CITATION_ARTICLE_TYPE] = self.article_type

        if self.authors:
            result[CITATION_AUTHORS] = sorted(
                author.name
                for author in self.authors
            )

        return result


class Evidence(Base):
    """This table contains the evidence text that proves a specific relationship and refers the source that is cited."""

    __tablename__ = EVIDENCE_TABLE_NAME

    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False, doc='Supporting text from a given publication')

    citation_id = Column(Integer, ForeignKey('{}.id'.format(CITATION_TABLE_NAME)), nullable=False)
    citation = relationship(Citation, backref=backref('evidences'))

    __table_args__ = (
        UniqueConstraint(citation_id, text),
    )

    def __str__(self):
        return '{}:{}:{}'.format(self.citation.db, self.citation.db_id, self.text)

    def to_json(self, include_id: bool = False):
        """Create a dictionary that is used to recreate the edge data dictionary for a :class:`BELGraph`.

        :param include_id: If true, includes the model identifier
        :return: Dictionary containing citation and evidence for a :class:`BELGraph` edge.
        :rtype: dict
        """
        result = {
            CITATION: self.citation.to_json(include_id=include_id),
            EVIDENCE: self.text,
        }

        if include_id:
            result['id'] = self.id

        return result


edge_annotation = Table(
    EDGE_ANNOTATION_TABLE_NAME, Base.metadata,
    Column('edge_id', Integer, ForeignKey('{}.id'.format(EDGE_TABLE_NAME)), primary_key=True),
    Column('name_id', Integer, ForeignKey('{}.id'.format(NAME_TABLE_NAME)), primary_key=True),
)


class Edge(Base):
    """Relationships between BEL nodes and their properties, annotations, and provenance."""

    __tablename__ = EDGE_TABLE_NAME

    id = Column(Integer, primary_key=True)

    bel = Column(Text, nullable=False, doc='Valid BEL statement that represents the given edge')
    relation = Column(String(32), nullable=False)

    source_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)), nullable=False)
    source = relationship(
        Node, foreign_keys=[source_id],
        backref=backref('out_edges', lazy='dynamic', cascade='all, delete-orphan'),
    )

    target_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)), nullable=False)
    target = relationship(
        Node, foreign_keys=[target_id],
        backref=backref('in_edges', lazy='dynamic', cascade='all, delete-orphan'),
    )

    evidence_id = Column(Integer, ForeignKey('{}.id'.format(EVIDENCE_TABLE_NAME)), nullable=True)
    evidence = relationship(Evidence, backref=backref('edges', lazy='dynamic'))

    annotations = relationship(
        NamespaceEntry, secondary=edge_annotation, lazy="dynamic",
        backref=backref('edges', lazy='dynamic'),
    )

    # free_annotations = Column(JSON, nullable=True, doc='Ungrounded extra annotations')

    source_modifier = Column(JSON, nullable=True, doc='Modifiers for the source of the edge')
    target_modifier = Column(JSON, nullable=True, doc='Modifiers for the target of the edge')

    md5 = Column(String(255), index=True, unique=True, doc='The hash of the source, target, and associated metadata')

    data = Column(JSON, nullable=False, doc='The stringified JSON representing this edge')

    def __str__(self):
        return self.bel

    def __repr__(self):
        return '<Edge {}: {}>'.format(self.md5, self.bel)

    def get_annotations_json(self):
        """Format the annotations properly.

        :rtype: Optional[dict[str,dict[str,bool]]
        """
        annotations = defaultdict(dict)

        for entry in self.annotations:
            annotations[entry.namespace.keyword][entry.name] = True

        return dict(annotations) or None

    def to_json(self, include_id: bool = False) -> Mapping[str, Any]:
        """Create a dictionary of one BEL Edge that can be used to create an edge in a :class:`BELGraph`.

        :param bool include_id: Include the database identifier?
        :return: Dictionary that contains information about an edge of a :class:`BELGraph`. Including participants
                 and edge data information.
        """
        source_dict = self.source.to_json()
        source_dict['md5'] = source_dict.md5
        target_dict = self.target.to_json()
        target_dict['md5'] = target_dict.md5

        result = {
            'source': source_dict,
            'target': target_dict,
            'key': self.md5,
            'data': self.data,
        }

        if include_id:
            result['id'] = self.id

        return result

    def insert_into_graph(self, graph: BELGraph) -> str:
        """Insert this edge into a BEL graph."""
        u = self.source.as_bel()
        v = self.target.as_bel()

        if self.evidence:
            return graph.add_qualified_edge(u, v, **self.data)
        else:
            return graph.add_unqualified_edge(u, v, self.relation)
