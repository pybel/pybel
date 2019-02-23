# -*- coding: utf-8 -*-

"""This module contains the SQLAlchemy database models that support the definition cache and graph cache."""

import datetime
import hashlib
import json
from collections import defaultdict
from typing import Iterable, Mapping

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, LargeBinary, String, Table, Text, UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship

from .utils import int_or_str
from ..constants import (
    CITATION, CITATION_AUTHORS, CITATION_DATE, CITATION_FIRST_AUTHOR, CITATION_LAST_AUTHOR, CITATION_NAME,
    CITATION_PAGES, CITATION_REFERENCE, CITATION_TITLE, CITATION_TYPE, CITATION_TYPE_PUBMED, CITATION_VOLUME, EFFECT,
    EVIDENCE, FRAGMENT, FUSION, GMOD, HGVS, IDENTIFIER, LOCATION, METADATA_AUTHORS, METADATA_CONTACT,
    METADATA_COPYRIGHT, METADATA_DESCRIPTION, METADATA_DISCLAIMER, METADATA_LICENSES, METADATA_NAME, METADATA_VERSION,
    MODIFIER, NAME, NAMESPACE, OBJECT, PARTNER_3P, PARTNER_5P, PMOD, RANGE_3P, RANGE_5P, SUBJECT,
)
from ..dsl import fragment, fusion_range, gmod, hgvs, missing_fusion_range, pmod
from ..io.gpickle import from_bytes, to_bytes
from ..tokens import parse_result_to_dsl

__all__ = [
    'Base',
    'Namespace',
    'NamespaceEntry',
    'Network',
    'Node',
    'Modification',
    'Author',
    'Citation',
    'Evidence',
    'Edge',
    'Property',
    'edge_annotation',
    'edge_property',
    'network_edge',
    'network_node',
]

NAME_TABLE_NAME = 'pybel_name'
NAMESPACE_TABLE_NAME = 'pybel_namespace'

NODE_TABLE_NAME = 'pybel_node'
MODIFICATION_TABLE_NAME = 'pybel_modification'
NODE_MODIFICATION_TABLE_NAME = 'pybel_node_modification'

PROPERTY_TABLE_NAME = 'pybel_property'

EDGE_TABLE_NAME = 'pybel_edge'
EDGE_ANNOTATION_TABLE_NAME = 'pybel_edge_name'
EDGE_PROPERTY_TABLE_NAME = 'pybel_edge_property'

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
    keyword = Column(String(255), nullable=True, index=True,
                     doc='Keyword that is used in a BEL file to identify a specific namespace')

    # A namespace either needs a URL or a pattern
    pattern = Column(String(255), nullable=True, index=True,
                     doc="Contains regex pattern for value identification.")

    miriam_id = Column(String(16), nullable=True,
                       doc=r'MIRIAM resource identifier matching the regular expression ``^MIR:001\d{5}$``')
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
        return self.keyword

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

    name = Column(String(1023), index=True, nullable=False,
                  doc='Name that is defined in the corresponding namespace definition file')
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
        return '[{namespace_id}]{namespace_name}:[{identifier}]{name}'.format(
            namespace_id=self.namespace.id,
            namespace_name=self.namespace.keyword,
            identifier=self.identifier,
            name=self.name,
        )


network_edge = Table(
    NETWORK_EDGE_TABLE_NAME, Base.metadata,
    Column('network_id', Integer, ForeignKey('{}.id'.format(NETWORK_TABLE_NAME)), primary_key=True),
    Column('edge_id', Integer, ForeignKey('{}.id'.format(EDGE_TABLE_NAME)), primary_key=True)
)

network_node = Table(
    NETWORK_NODE_TABLE_NAME, Base.metadata,
    Column('network_id', Integer, ForeignKey('{}.id'.format(NETWORK_TABLE_NAME)), primary_key=True),
    Column('node_id', Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)), primary_key=True)
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

    __table_args__ = (
        UniqueConstraint(name, version),
    )

    def to_json(self, include_id: bool = False):
        """Return this network as JSON.

        :param include_id: If true, includes the model identifier
        :rtype: dict[str,str]
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

    def as_bel(self):
        """Get this network and loads it into a :class:`BELGraph`.

        :rtype: pybel.BELGraph
        """
        return from_bytes(self.blob)

    def store_bel(self, graph):
        """Insert a BEL graph.

        :param pybel.BELGraph graph: A BEL Graph
        """
        self.blob = to_bytes(graph)


node_modification = Table(
    NODE_MODIFICATION_TABLE_NAME, Base.metadata,
    Column('node_id', Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)), primary_key=True),
    Column('modification_id', Integer, ForeignKey('{}.id'.format(MODIFICATION_TABLE_NAME)), primary_key=True)
)


class Modification(Base):
    """The modifications that are present in the network are stored in this table."""

    __tablename__ = MODIFICATION_TABLE_NAME
    id = Column(Integer, primary_key=True)

    type = Column(String(255), nullable=False, doc='Type of the stored modification e.g. Fusion, gmod, pmod, etc')

    variantString = Column(String(255), nullable=True, doc='HGVS string if sequence modification')  # noqa: N815

    p3_partner_id = Column(Integer, ForeignKey('{}.id'.format(NAME_TABLE_NAME)), nullable=True)
    p3_partner = relationship(NamespaceEntry, foreign_keys=[p3_partner_id])

    p3_reference = Column(String(10), nullable=True)
    p3_start = Column(String(255), nullable=True)
    p3_stop = Column(String(255), nullable=True)

    p5_partner_id = Column(Integer, ForeignKey('{}.id'.format(NAME_TABLE_NAME)), nullable=True)
    p5_partner = relationship(NamespaceEntry, foreign_keys=[p5_partner_id])

    p5_reference = Column(String(10), nullable=True)
    p5_start = Column(String(255), nullable=True)
    p5_stop = Column(String(255), nullable=True)

    identifier_id = Column(Integer, ForeignKey('{}.id'.format(NAME_TABLE_NAME)), nullable=True)
    identifier = relationship(NamespaceEntry, foreign_keys=[identifier_id])

    residue = Column(String(3), nullable=True, doc='Three letter amino acid code if PMOD')
    position = Column(Integer, nullable=True, doc='Position of PMOD or GMOD')

    sha512 = Column(String(255), index=True)

    def _fusion_to_json(self):
        """Convert this modification to a FUSION data dictionary.

        Don't use this without checking ``self.type == FUSION`` first.

        :rtype: dict
        """
        if self.p5_reference:
            range_5p = fusion_range(
                reference=str(self.p5_reference),
                start=int_or_str(self.p5_start),
                stop=int_or_str(self.p5_stop),
            )
        else:
            range_5p = missing_fusion_range()

        if self.p3_reference:
            range_3p = fusion_range(
                reference=str(self.p3_reference),
                start=int_or_str(self.p3_start),
                stop=int_or_str(self.p3_stop),
            )
        else:
            range_3p = missing_fusion_range()

        return {
            PARTNER_5P: self.p5_partner.to_json(),  # just the identifier pair
            PARTNER_3P: self.p3_partner.to_json(),  # just the identifier pair
            RANGE_5P: range_5p,
            RANGE_3P: range_3p,
        }

    def to_json(self):
        """Recreate a is_variant dictionary for :class:`BELGraph`.

        :return: Dictionary that describes a variant or a fusion.
        :rtype: Variant or FusionBase
        """
        if self.type == FUSION:
            return self._fusion_to_json()

        if self.type == FRAGMENT:
            return fragment(
                start=int_or_str(self.p3_start),
                stop=int_or_str(self.p3_stop),
            )

        if self.type == HGVS:
            return hgvs(str(self.variantString))

        if self.type == GMOD:
            return gmod(
                namespace=self.identifier.namespace.keyword,
                name=self.identifier.name,
                identifier=self.identifier.identifier,
            )

        if self.type == PMOD:
            return pmod(
                namespace=self.identifier.namespace.keyword,
                name=self.identifier.name,
                identifier=self.identifier.identifier,
                code=self.residue,
                position=self.position
            )

        raise TypeError('unhandled type ({}) for modification {}'.format(self.type, self))


class Node(Base):
    """Represents a BEL Term."""

    __tablename__ = NODE_TABLE_NAME
    id = Column(Integer, primary_key=True)

    type = Column(String(255), nullable=False, doc='The type of the represented biological entity e.g. Protein or Gene')
    is_variant = Column(Boolean, default=False, doc='Identifies weather or not the given node is a variant')
    has_fusion = Column(Boolean, default=False, doc='Identifies weather or not the given node is a fusion')
    bel = Column(String(255), nullable=False, doc='Canonical BEL term that represents the given node')
    sha512 = Column(String(255), nullable=True, index=True)

    namespace_entry_id = Column(Integer, ForeignKey('{}.id'.format(NAME_TABLE_NAME)), nullable=True)
    namespace_entry = relationship(NamespaceEntry, foreign_keys=[namespace_entry_id])

    modifications = relationship(Modification, secondary=node_modification, lazy='dynamic',
                                 backref=backref('nodes', lazy='dynamic'))

    data = Column(Text, nullable=False, doc='PyBEL BaseEntity as JSON')

    @staticmethod
    def _start_from_base_entity(base_entity):
        """Convert a base entity to a node model.

        :type base_entity: pybel.dsl.BaseEntity
        :rtype: Node
        """
        return Node(
            type=base_entity.function,
            bel=base_entity.as_bel(),
            sha512=base_entity.sha512,
            data=json.dumps(base_entity),
        )

    @classmethod
    def bel_contains(cls, bel_query):
        """Build a filter for nodes whose BEL contain the query.

        :type bel_query: str
        """
        return cls.bel.contains(bel_query)

    def __str__(self):
        return self.bel

    def __repr__(self):
        return '<Node {}: {}>'.format(self.sha512[:10], self.bel)

    def _get_list_by_relation(self, relation):
        return [
            edge.target.to_json()
            for edge in self.out_edges.filter(Edge.relation == relation)
        ]

    def as_bel(self):
        """Serialize this node as a PyBEL DSL object.

        :rtype: pybel.dsl.BaseEntity
        """
        return parse_result_to_dsl(json.loads(self.data))

    def to_json(self):
        """Serialize this node as a JSON object using as_bel()."""
        return self.as_bel()


author_citation = Table(
    AUTHOR_CITATION_TABLE_NAME, Base.metadata,
    Column('author_id', Integer, ForeignKey('{}.id'.format(AUTHOR_TABLE_NAME)), primary_key=True),
    Column('citation_id', Integer, ForeignKey('{}.id'.format(CITATION_TABLE_NAME)), primary_key=True)
)


class Author(Base):
    """Contains all author names."""

    __tablename__ = AUTHOR_TABLE_NAME

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    sha512 = Column(String(255), nullable=False, index=True, unique=True)

    @classmethod
    def from_name(cls, name):
        """Create an author by name, automatically populating the hash."""
        return Author(name=name, sha512=cls.hash_name(name))

    @staticmethod
    def hash_name(name):
        """Hash a name.

        :param str name: Name of an author
        :rtype: str
        """
        return hashlib.sha512(name.encode('utf-8')).hexdigest()

    @classmethod
    def name_contains(cls, name_query):
        """Build a filter for authors whose names contain the given query.

        :type name_query: str
        """
        return cls.name.contains(name_query)

    @classmethod
    def has_name(cls, name):
        """Build a filter for if an author has a name.

        :type name: str
        """
        return cls.sha512 == cls.hash_name(name)

    @classmethod
    def has_name_in(cls, names):
        """Build a filter if the author has any of the given names."""
        return cls.sha512.in_({
            cls.hash_name(name)
            for name in names
        })

    def __str__(self):
        return self.name


class Citation(Base):
    """The information about the citations that are used to prove a specific relation are stored in this table."""

    __tablename__ = CITATION_TABLE_NAME

    id = Column(Integer, primary_key=True)

    type = Column(String(16), nullable=False, doc='Type of the stored publication e.g. PubMed')
    reference = Column(String(255), nullable=False, doc='Reference identifier of the publication e.g. PubMed_ID')
    sha512 = Column(String(255), index=True)

    name = Column(String(255), nullable=True, doc='Journal name')
    title = Column(Text, nullable=True, doc='Title of the publication')
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
        UniqueConstraint(CITATION_TYPE, CITATION_REFERENCE),
    )

    def __str__(self):
        return '{}:{}'.format(self.type, self.reference)

    @property
    def is_pubmed(self):
        """Return if this is a PubMed citation.

        :rtype: bool
        """
        return CITATION_TYPE_PUBMED == self.type

    @property
    def is_enriched(self):
        """Return if this citation has been enriched for name, title, and other metadata.

        :rtype: bool
        """
        return self.title is not None and self.name is not None

    def to_json(self, include_id=False):
        """Create a citation dictionary that is used to recreate the edge data dictionary of a :class:`BELGraph`.

        :param bool include_id: If true, includes the model identifier
        :return: Citation dictionary for the recreation of a :class:`BELGraph`.
        :rtype: dict[str,str]
        """
        result = {
            CITATION_REFERENCE: self.reference,
            CITATION_TYPE: self.type
        }

        if include_id:
            result['id'] = self.id

        if self.name:
            result[CITATION_NAME] = self.name

        if self.title:
            result[CITATION_TITLE] = self.title

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

    sha512 = Column(String(255), index=True)

    def __str__(self):
        return '{}:{}'.format(self.citation, self.sha512[:8])

    def to_json(self, include_id: bool = False):
        """Create a dictionary that is used to recreate the edge data dictionary for a :class:`BELGraph`.

        :param include_id: If true, includes the model identifier
        :return: Dictionary containing citation and evidence for a :class:`BELGraph` edge.
        :rtype: dict
        """
        result = {
            CITATION: self.citation.to_json(include_id=include_id),
            EVIDENCE: self.text
        }

        if include_id:
            result['id'] = self.id

        return result


edge_annotation = Table(
    EDGE_ANNOTATION_TABLE_NAME, Base.metadata,
    Column('edge_id', Integer, ForeignKey('{}.id'.format(EDGE_TABLE_NAME)), primary_key=True),
    Column('name_id', Integer, ForeignKey('{}.id'.format(NAME_TABLE_NAME)), primary_key=True)
)

edge_property = Table(
    EDGE_PROPERTY_TABLE_NAME, Base.metadata,
    Column('edge_id', Integer, ForeignKey('{}.id'.format(EDGE_TABLE_NAME)), primary_key=True),
    Column('property_id', Integer, ForeignKey('{}.id'.format(PROPERTY_TABLE_NAME)), primary_key=True)
)


class Property(Base):
    """The property table contains additional information that is used to describe the context of a relation."""

    __tablename__ = PROPERTY_TABLE_NAME

    id = Column(Integer, primary_key=True)

    is_subject = Column(Boolean, doc='Identifies which participant of the edge if affected by the given property')
    modifier = Column(String(255), doc='The modifier: one of activity, degradation, location, or translocation')

    relative_key = Column(String(255), nullable=True, doc='Relative key of effect e.g. to_tloc or from_tloc')

    sha512 = Column(String(255), index=True)

    effect_id = Column(Integer, ForeignKey('{}.id'.format(NAME_TABLE_NAME)), nullable=True)
    effect = relationship(NamespaceEntry)

    @property
    def side(self):
        """Return either :data:`pybel.constants.SUBJECT` or :data:`pybel.constants.OBJECT`.

        :rtype: str
        """
        return SUBJECT if self.is_subject else OBJECT

    def to_json(self):
        """Create a property dict that is used to recreate an edge dictionary for a :class:`BELGraph`.

        :return: Property dictionary of an edge that is participant (sub/obj) related.
        :rtype: dict
        """
        participant = self.side

        prop_dict = {
            participant: {
                MODIFIER: self.modifier  # FIXME this is probably wrong for location
            }
        }

        if self.modifier == LOCATION:
            prop_dict[participant] = {
                LOCATION: self.effect.to_json()
            }
        if self.relative_key:  # for translocations
            prop_dict[participant][EFFECT] = {
                self.relative_key: self.effect.to_json()
            }
        elif self.effect:  # for activities
            prop_dict[participant][EFFECT] = self.effect.to_json()

        # degradations don't have modifications

        return prop_dict


class Edge(Base):
    """Relationships between BEL nodes and their properties, annotations, and provenance."""

    __tablename__ = EDGE_TABLE_NAME

    id = Column(Integer, primary_key=True)

    bel = Column(Text, nullable=False, doc='Valid BEL statement that represents the given edge')
    relation = Column(String(255), nullable=False)

    source_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)), nullable=False)
    source = relationship(Node, foreign_keys=[source_id],
                          backref=backref('out_edges', lazy='dynamic', cascade='all, delete-orphan'))

    target_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)), nullable=False)
    target = relationship(Node, foreign_keys=[target_id],
                          backref=backref('in_edges', lazy='dynamic', cascade='all, delete-orphan'))

    evidence_id = Column(Integer, ForeignKey('{}.id'.format(EVIDENCE_TABLE_NAME)), nullable=True)
    evidence = relationship(Evidence, backref=backref('edges', lazy='dynamic'))

    annotations = relationship(NamespaceEntry, secondary=edge_annotation, lazy="dynamic",
                               backref=backref('edges', lazy='dynamic'))
    properties = relationship(Property, secondary=edge_property, lazy="dynamic")  # , cascade='all, delete-orphan')

    sha512 = Column(String(255), index=True, doc='The hash of the source, target, and associated metadata')

    data = Column(Text, nullable=False, doc='The stringified JSON representing this edge')

    def __str__(self):
        return self.bel

    def __repr__(self):
        return '<Edge {}: {}>'.format(self.sha512[:10], self.bel)

    def get_annotations_json(self):
        """Format the annotations properly.

        :rtype: Optional[dict[str,dict[str,bool]]
        """
        annotations = defaultdict(dict)

        for entry in self.annotations:
            annotations[entry.namespace.keyword][entry.name] = True

        return dict(annotations) or None

    def to_json(self, include_id=False):
        """Create a dictionary of one BEL Edge that can be used to create an edge in a :class:`BELGraph`.

        :param bool include_id: Include the database identifier?
        :return: Dictionary that contains information about an edge of a :class:`BELGraph`. Including participants
                 and edge data information.
        :rtype: dict
        """
        source_dict = self.source.to_json()
        source_dict['sha512'] = source_dict.sha512
        target_dict = self.target.to_json()
        target_dict['sha512'] = target_dict.sha512

        result = {
            'source': source_dict,
            'target': target_dict,
            'key': self.sha512,
            'data': json.loads(self.data),
        }

        if include_id:
            result['id'] = self.id

        return result

    def insert_into_graph(self, graph):
        """Insert this edge into a BEL graph.

        :param pybel.BELGraph graph: A BEL graph
        """
        u = self.source.as_bel()
        v = self.target.as_bel()

        if self.evidence:
            return graph.add_qualified_edge(u, v, **json.loads(self.data))
        else:
            return graph.add_unqualified_edge(u, v, self.relation)
