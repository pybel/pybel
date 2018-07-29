# -*- coding: utf-8 -*-

"""This module contains the SQLAlchemy database models that support the definition cache and graph cache."""

import datetime

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, LargeBinary, String, Table, Text, UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship

from .utils import int_or_str
from ..constants import (
    ANNOTATIONS, BELNS_ENCODING_STR, CITATION, CITATION_AUTHORS, CITATION_DATE, CITATION_FIRST_AUTHOR,
    CITATION_LAST_AUTHOR, CITATION_NAME, CITATION_PAGES, CITATION_REFERENCE, CITATION_TITLE, CITATION_TYPE,
    CITATION_TYPE_PUBMED, CITATION_VOLUME, COMPLEX, COMPOSITE, EFFECT, EVIDENCE, FRAGMENT, FUNCTION, FUSION, HASH,
    HAS_COMPONENT, HAS_PRODUCT, HAS_REACTANT, HGVS, IDENTIFIER, KIND, LOCATION, MEMBERS, METADATA_AUTHORS,
    METADATA_CONTACT, METADATA_COPYRIGHT, METADATA_DESCRIPTION, METADATA_DISCLAIMER, METADATA_LICENSES, METADATA_NAME,
    METADATA_VERSION, MODIFIER, NAME, NAMESPACE, OBJECT, PARTNER_3P, PARTNER_5P, PMOD, PMOD_CODE, PMOD_POSITION,
    PRODUCTS, RANGE_3P, RANGE_5P, REACTANTS, REACTION, RELATION, SUBJECT, VARIANTS,
)
from ..dsl import fragment, fusion_range, hgvs, missing_fusion_range
from ..io.gpickle import from_bytes, to_bytes
from ..tokens import node_to_tuple, sort_dict_list, sort_variant_dict_list

__all__ = [
    'Base',
    'Namespace',
    'NamespaceEntry',
    'NamespaceEntryEquivalence',
    'Annotation',
    'AnnotationEntry',
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

NAMESPACE_TABLE_NAME = 'pybel_namespace'
NAMESPACE_ENTRY_TABLE_NAME = 'pybel_namespaceEntry'
NAMESPACE_EQUIVALENCE_TABLE_NAME = 'pybel_namespaceEquivalence'
NAMESPACE_EQUIVALENCE_CLASS_TABLE_NAME = 'pybel_namespaceEquivalenceClass'
NAMESPACE_HIERARCHY_TABLE_NAME = 'pybel_namespace_hierarchy'

ANNOTATION_TABLE_NAME = 'pybel_annotation'
ANNOTATION_ENTRY_TABLE_NAME = 'pybel_annotationEntry'
ANNOTATION_HIERARCHY_TABLE_NAME = 'pybel_annotation_hierarchy'

NETWORK_TABLE_NAME = 'pybel_network'
NETWORK_NODE_TABLE_NAME = 'pybel_network_node'
NETWORK_EDGE_TABLE_NAME = 'pybel_network_edge'
NETWORK_NAMESPACE_TABLE_NAME = 'pybel_network_namespace'
NETWORK_ANNOTATION_TABLE_NAME = 'pybel_network_annotation'
NETWORK_CITATION_TABLE_NAME = 'pybel_network_citation'

NODE_TABLE_NAME = 'pybel_node'
NODE_MODIFICATION_TABLE_NAME = 'pybel_node_modification'

MODIFICATION_TABLE_NAME = 'pybel_modification'

EDGE_TABLE_NAME = 'pybel_edge'
EDGE_ANNOTATION_TABLE_NAME = 'pybel_edge_annotationEntry'
EDGE_PROPERTY_TABLE_NAME = 'pybel_edge_property'

AUTHOR_TABLE_NAME = 'pybel_author'
AUTHOR_CITATION_TABLE_NAME = 'pybel_author_citation'

CITATION_TABLE_NAME = 'pybel_citation'
EVIDENCE_TABLE_NAME = 'pybel_evidence'
PROPERTY_TABLE_NAME = 'pybel_property'

LONGBLOB = 4294967295

Base = declarative_base()

namespace_hierarchy = Table(
    NAMESPACE_HIERARCHY_TABLE_NAME,
    Base.metadata,
    Column('left_id', Integer, ForeignKey('{}.id'.format(NAMESPACE_ENTRY_TABLE_NAME)), primary_key=True),
    Column('right_id', Integer, ForeignKey('{}.id'.format(NAMESPACE_ENTRY_TABLE_NAME)), primary_key=True)
)

annotation_hierarchy = Table(
    ANNOTATION_HIERARCHY_TABLE_NAME,
    Base.metadata,
    Column('left_id', Integer, ForeignKey('{}.id'.format(ANNOTATION_ENTRY_TABLE_NAME)), primary_key=True),
    Column('right_id', Integer, ForeignKey('{}.id'.format(ANNOTATION_ENTRY_TABLE_NAME)), primary_key=True)
)


class Namespace(Base):
    """Represents a BEL Namespace"""
    __tablename__ = NAMESPACE_TABLE_NAME

    id = Column(Integer, primary_key=True)

    uploaded = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, doc='The date of upload')
    keyword = Column(String(16), nullable=True, index=True,
                     doc='Keyword that is used in a BEL file to identify a specific namespace')

    # A namespace either needs a URL or a pattern
    pattern = Column(String(255), nullable=True, unique=True, index=True,
                     doc="Contains regex pattern for value identification.")

    url = Column(String(255), nullable=True, unique=True, index=True, doc='BELNS Resource location as URL')

    name = Column(String(255), nullable=True, doc='Name of the given namespace')
    domain = Column(String(255), nullable=True, doc='Domain for which this namespace is valid')
    species = Column(String(255), nullable=True, doc='Taxonomy identifiers for which this namespace is valid')
    description = Column(Text, nullable=True, doc='Optional short description of the namespace')
    version = Column(String(255), nullable=True, doc='Version of the namespace')
    created = Column(DateTime, nullable=True, doc='DateTime of the creation of the namespace definition file')
    query_url = Column(Text, nullable=True, doc='URL that can be used to query the namespace (externally from PyBEL)')

    author = Column(String(255), doc='The author of the namespace')
    license = Column(String(255), nullable=True, doc='License information')
    contact = Column(String(255), nullable=True, doc='Contact information')

    citation = Column(String(255))
    citation_description = Column(Text, nullable=True)
    citation_version = Column(String(255), nullable=True)
    citation_published = Column(Date, nullable=True)
    citation_url = Column(String(255), nullable=True)

    # entries = relationship('NamespaceEntry', backref='namespace', cascade='all, delete-orphan')

    has_equivalences = Column(Boolean, default=False)

    def __str__(self):
        return self.keyword

    def to_values(self):
        """Returns this namespace as a dictionary of names to their encodings. Encodings are represented as a
        string, and lookup operations take constant time O(8).

        :rtype: dict[str,str]
        """
        return {
            entry.name: entry.encoding if entry.encoding else BELNS_ENCODING_STR
            for entry in self.entries
        }

    def to_tree_list(self):
        """Returns an edge set of the tree represented by this namespace's hierarchy

        :rtype: set[tuple[str,str]]
        """
        return {
            (parent.name, child.name)
            for parent in self.entries
            for child in parent.children
        }

    def to_json(self, include_id=False):
        """Returns the most useful entries as a dictionary

        :param bool include_id: If true, includes the model identifier
        :rtype: dict[str,str]
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
    """Represents a name within a BEL namespace"""
    __tablename__ = NAMESPACE_ENTRY_TABLE_NAME

    id = Column(Integer, primary_key=True)

    name = Column(String(1023), index=True, nullable=False,
                  doc='Name that is defined in the corresponding namespace definition file')
    identifier = Column(String(255), index=True, nullable=True, doc='The database accession number')
    encoding = Column(String(8), nullable=True, doc='The biological entity types for which this name is valid')

    namespace_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_TABLE_NAME)), nullable=False, index=True)
    namespace = relationship('Namespace', backref=backref('entries', lazy='dynamic'))

    equivalence_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_EQUIVALENCE_CLASS_TABLE_NAME)), nullable=True)
    equivalence = relationship('NamespaceEntryEquivalence', backref=backref('members'))

    children = relationship(
        'NamespaceEntry',
        secondary=namespace_hierarchy,
        primaryjoin=(id == namespace_hierarchy.c.left_id),
        secondaryjoin=(id == namespace_hierarchy.c.right_id),
    )

    def __str__(self):
        return '[{}]{}:[{}]{}'.format(self.namespace.id, self.namespace, self.identifier, self.name)

    def to_json(self, include_id=False):
        """Describes the namespaceEntry as dictionary of Namespace-Keyword and Name.

        :param bool include_id: If true, includes the model identifier
        :rtype: dict[str,str]
        """
        result = {
            NAMESPACE: self.namespace.keyword,
            NAME: self.name
        }

        if self.identifier:
            result[IDENTIFIER] = self.identifier

        if include_id:
            result['id'] = self.id

        return result


class NamespaceEntryEquivalence(Base):
    """Represents the equivalance classes between entities"""
    __tablename__ = NAMESPACE_EQUIVALENCE_CLASS_TABLE_NAME

    id = Column(Integer, primary_key=True)
    label = Column(String(255), nullable=False, unique=True, index=True)


class Annotation(Base):
    """Represents a BEL Annotation"""
    __tablename__ = ANNOTATION_TABLE_NAME

    id = Column(Integer, primary_key=True)
    uploaded = Column(DateTime, default=datetime.datetime.utcnow, doc='The date of upload')

    url = Column(String(255), nullable=False, unique=True, index=True,
                 doc='Source url of the given annotation definition file (.belanno)')
    keyword = Column(String(50), index=True, doc='Keyword that is used in a BEL file to identify a specific annotation')
    type = Column(String(255), doc='Annotation type')
    description = Column(Text, nullable=True, doc='Optional short description of the given annotation')
    usage = Column(Text, nullable=True)
    version = Column(String(255), nullable=True, doc='Version of the annotation')
    created = Column(DateTime, doc='DateTime of the creation of the given annotation definition')

    name = Column(String(255), doc='Name of the annotation definition')
    author = Column(String(255), doc='Author information')
    license = Column(String(255), nullable=True, doc='License information')
    contact = Column(String(255), nullable=True, doc='Contact information')

    citation = Column(String(255))
    citation_description = Column(Text, nullable=True)
    citation_version = Column(String(255), nullable=True)
    citation_published = Column(Date, nullable=True)
    citation_url = Column(String(255), nullable=True)

    def get_entry_names(self):
        """Gets a set of the names of all entries

        :rtype: set[str]
        """
        return {
            entry.name
            for entry in self.entries
        }

    def to_tree_list(self):
        """Returns an edge set of the tree represented by this namespace's hierarchy

        :rtype: set[tuple[str,str]]
        """
        return {
            (parent.name, child.name)
            for parent in self.entries
            for child in parent.children
        }

    def to_json(self, include_id=False):
        """Returns this annotation as a JSON dictionary

        :param bool include_id: If true, includes the model identifier
        :rtype: dict[str,str]
        """
        result = {
            'url': self.url,
            'keyword': self.keyword,
            'version': self.version,
            'name': self.name
        }

        if include_id:
            result['id'] = self.id

        return result

    def __str__(self):
        return self.keyword


class AnnotationEntry(Base):
    """Represents a value within a BEL Annotation"""
    __tablename__ = ANNOTATION_ENTRY_TABLE_NAME

    id = Column(Integer, primary_key=True)

    name = Column(String(255), nullable=False, index=True,
                  doc='Name that is defined in the corresponding annotation definition file')
    label = Column(Text, nullable=True)

    annotation_id = Column(Integer, ForeignKey('{}.id'.format(ANNOTATION_TABLE_NAME)), index=True)
    annotation = relationship('Annotation', backref=backref('entries', lazy='dynamic'))

    children = relationship(
        'AnnotationEntry',
        secondary=annotation_hierarchy,
        primaryjoin=(id == annotation_hierarchy.c.left_id),
        secondaryjoin=(id == annotation_hierarchy.c.right_id)
    )

    def to_json(self, include_id=False):
        """Describes the annotationEntry as dictionary of Annotation-Keyword and Annotation-Name.

        :param bool include_id: If true, includes the model identifier
        :rtype: dict[str,str]
        """
        result = {
            'annotation_keyword': self.annotation.keyword,
            'annotation': self.name
        }

        if include_id:
            result['id'] = self.id

        return result

    @staticmethod
    def name_contains(name_query):
        """Makes a filter if the name contains a certain substring

        :param str name_query:
        """
        return AnnotationEntry.name.contains(name_query)

    def __str__(self):
        return '{}:{}'.format(self.annotation, self.name)


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
    """Represents a collection of edges, specified by a BEL Script"""
    __tablename__ = NETWORK_TABLE_NAME

    id = Column(Integer, primary_key=True)

    name = Column(String(255), nullable=False, index=True, doc='Name of the given Network (from the BEL file)')
    version = Column(String(16), nullable=False, doc='Release version of the given Network (from the BEL file)')

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

    def to_json(self, include_id=False):
        """Returns this network as JSON

        :param bool include_id: If true, includes the model identifier
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

    @staticmethod
    def name_contains(name_query):
        """
        :param str name_query:
        """
        return Network.name.contains(name_query)

    @staticmethod
    def description_contains(description_query):
        """
        :param str description_query:
        """
        return Network.description.contains(description_query)

    @staticmethod
    def id_in(network_ids):
        """
        :param iter[int] network_ids:
        """
        return Network.id.in_(network_ids)

    def __repr__(self):
        return '{} v{}'.format(self.name, self.version)

    def __str__(self):
        return repr(self)

    def as_bel(self):
        """Gets this network and loads it into a :class:`BELGraph`

        :rtype: pybel.BELGraph
        """
        return from_bytes(self.blob)

    def store_bel(self, graph):
        """Inserts a bel graph

        :param pybel.BELGraph graph: A BEL Graph
        """
        self.blob = to_bytes(graph)


node_modification = Table(
    NODE_MODIFICATION_TABLE_NAME, Base.metadata,
    Column('node_id', Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)), primary_key=True),
    Column('modification_id', Integer, ForeignKey('{}.id'.format(MODIFICATION_TABLE_NAME)), primary_key=True)
)


class Node(Base):
    """Represents a BEL Term"""
    __tablename__ = NODE_TABLE_NAME

    id = Column(Integer, primary_key=True)

    type = Column(String(255), nullable=False, doc='The type of the represented biological entity e.g. Protein or Gene')
    is_variant = Column(Boolean, default=False, doc='Identifies weather or not the given node is a variant')
    has_fusion = Column(Boolean, default=False, doc='Identifies weather or not the given node is a fusion')
    bel = Column(String(255), nullable=False, doc='Canonical BEL term that represents the given node')
    sha512 = Column(String(255), nullable=True, index=True)

    namespace_entry_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_ENTRY_TABLE_NAME)), nullable=True)
    namespace_entry = relationship('NamespaceEntry', foreign_keys=[namespace_entry_id])

    modifications = relationship("Modification", secondary=node_modification, lazy='dynamic',
                                 backref=backref('nodes', lazy='dynamic'))

    @staticmethod
    def bel_contains(bel_query):
        return Node.bel.contains(bel_query)

    def __str__(self):
        return self.bel

    def __repr__(self):
        return '<Node {}: {}>'.format(self.sha512[:10], self.bel)

    def to_json(self, include_id=False, include_hash=False):
        """Serializes this node as a PyBEL node data dictionary

        :param bool include_id: Include the database identifier?
        :param bool include_hash: Include the node hash?
        :rtype: dict[str,str]
        """
        result = {FUNCTION: self.type}

        if include_id:
            result['id'] = self.id

        if include_hash:
            result[HASH] = self.sha512

        if self.namespace_entry:
            namespace_entry = self.namespace_entry.to_json()
            result.update(namespace_entry)

        if self.has_fusion:
            result[FUSION] = self.modifications[0].to_json()

        elif self.is_variant:
            result[VARIANTS] = sort_variant_dict_list(
                modification.to_json()
                for modification in self.modifications
            )

        elif self.type == REACTION:
            reactants = []
            products = []

            for edge in self.out_edges.filter(Edge.relation == HAS_PRODUCT):
                products.append(edge.target.to_json())

            for edge in self.out_edges.filter(Edge.relation == HAS_REACTANT):
                reactants.append(edge.target.to_json())

            result[REACTANTS] = sort_dict_list(reactants)
            result[PRODUCTS] = sort_dict_list(products)

        elif self.type == COMPOSITE or (self.type == COMPLEX and not self.namespace_entry):
            # FIXME handle when there's a named complex with member list as well
            result[MEMBERS] = sort_dict_list(
                edge.target.to_json()
                for edge in self.out_edges.filter(Edge.relation == HAS_COMPONENT)
            )

        return result

    def to_tuple(self):
        """Converts this node to a PyBEL tuple

        :rtype: tuple
        """
        return node_to_tuple(self.to_json())


class Modification(Base):
    """The modifications that are present in the network are stored in this table."""
    __tablename__ = MODIFICATION_TABLE_NAME

    id = Column(Integer, primary_key=True)

    type = Column(String(255), nullable=False, doc='Type of the stored modification e.g. Fusion, gmod, pmod, etc')

    variantString = Column(String(255), nullable=True, doc='HGVS string if sequence modification')

    p3_partner_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_ENTRY_TABLE_NAME)), nullable=True)
    p3_partner = relationship("NamespaceEntry", foreign_keys=[p3_partner_id])

    p3_reference = Column(String(10), nullable=True)
    p3_start = Column(String(255), nullable=True)
    p3_stop = Column(String(255), nullable=True)

    p5_partner_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_ENTRY_TABLE_NAME)), nullable=True)
    p5_partner = relationship("NamespaceEntry", foreign_keys=[p5_partner_id])

    p5_reference = Column(String(10), nullable=True)
    p5_start = Column(String(255), nullable=True)
    p5_stop = Column(String(255), nullable=True)

    identifier_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_ENTRY_TABLE_NAME)), nullable=True)
    identifier = relationship("NamespaceEntry", foreign_keys=[identifier_id])

    residue = Column(String(3), nullable=True, doc='Three letter amino acid code if PMOD')
    position = Column(Integer, nullable=True, doc='Position of PMOD or GMOD')

    sha512 = Column(String(255), index=True)

    def _fusion_to_json(self):
        """Converts this modification to a FUSION data dictionary. Don't use this without checking
        ``self.type == FUSION`` first"""
        fusion_dict = {
            PARTNER_3P: self.p3_partner.to_json(),
            PARTNER_5P: self.p5_partner.to_json(),
            RANGE_3P: {},
            RANGE_5P: {}
        }

        if self.p5_reference:
            fusion_dict[RANGE_5P] = fusion_range(
                reference=str(self.p5_reference),
                start=int_or_str(self.p5_start),
                stop=int_or_str(self.p5_stop),
            )
        else:
            fusion_dict[RANGE_5P] = missing_fusion_range()

        if self.p3_reference:
            fusion_dict[RANGE_3P] = fusion_range(
                reference=str(self.p3_reference),
                start=int_or_str(self.p3_start),
                stop=int_or_str(self.p3_stop),
            )
        else:
            fusion_dict[RANGE_3P] = missing_fusion_range()

        return fusion_dict

    def to_json(self):
        """Recreates a is_variant dictionary for :class:`BELGraph`

        :return: Dictionary that describes a variant or a fusion.
        :rtype: dict
        """
        if self.type == FUSION:
            return self._fusion_to_json()

        if self.type == FRAGMENT:
            return fragment(
                start=int_or_str(self.p3_start),
                stop=int_or_str(self.p3_stop)
            )

        if self.type == HGVS:
            return hgvs(str(self.variantString))

        # must be GMOD or PMOD now
        mod_dict = {
            KIND: self.type,
            IDENTIFIER: self.identifier.to_json()
        }

        if self.type == PMOD:
            if self.residue:
                mod_dict[PMOD_CODE] = self.residue

            if self.position:
                mod_dict[PMOD_POSITION] = self.position

        return mod_dict


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

    @staticmethod
    def name_contains(name_query):
        return Author.name.contains(name_query)

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
    first = relationship("Author", foreign_keys=[first_id])

    last_id = Column(Integer, ForeignKey('{}.id'.format(AUTHOR_TABLE_NAME)), nullable=True, doc='Last author')
    last = relationship("Author", foreign_keys=[last_id])

    authors = relationship("Author", secondary=author_citation, backref='citations')

    __table_args__ = (
        UniqueConstraint(CITATION_TYPE, CITATION_REFERENCE),
    )

    def __str__(self):
        return '{}:{}'.format(self.type, self.reference)

    @property
    def is_pubmed(self):
        """Return if this is a PubMed citation.

        :rtype:
        """
        return CITATION_TYPE_PUBMED == self.type

    @property
    def is_enriched(self):
        """Return if this citation has been enriched for name, title, and other metadata.

        :rtype:
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
    citation = relationship('Citation', backref=backref('evidences'))

    sha512 = Column(String(255), index=True)

    def __str__(self):
        return '{}:{}'.format(self.citation, self.text)

    def to_json(self, include_id=False):
        """Creates a dictionary that is used to recreate the edge data dictionary for a :class:`BELGraph`.

        :param bool include_id: If true, includes the model identifier
        :return: Dictionary containing citation and evidence for a :class:`BELGraph` edge.
        :rtype: dict
        """
        result = {
            CITATION: self.citation.to_json(),
            EVIDENCE: self.text
        }

        if include_id:
            result['id'] = self.id

        return result


edge_annotation = Table(
    EDGE_ANNOTATION_TABLE_NAME, Base.metadata,
    Column('edge_id', Integer, ForeignKey('{}.id'.format(EDGE_TABLE_NAME)), primary_key=True),
    Column('annotationEntry_id', Integer, ForeignKey('{}.id'.format(ANNOTATION_ENTRY_TABLE_NAME)), primary_key=True)
)

edge_property = Table(
    EDGE_PROPERTY_TABLE_NAME, Base.metadata,
    Column('edge_id', Integer, ForeignKey('{}.id'.format(EDGE_TABLE_NAME)), primary_key=True),
    Column('property_id', Integer, ForeignKey('{}.id'.format(PROPERTY_TABLE_NAME)), primary_key=True)
)


class Edge(Base):
    """Relationships are represented in this table. It shows the nodes that are in a relation to eachother and provides
    information about the context of the relation by refaring to the annotation, property and evidence tables.
    """
    __tablename__ = EDGE_TABLE_NAME

    id = Column(Integer, primary_key=True)

    bel = Column(Text, nullable=False, doc='Valid BEL statement that represents the given edge')
    relation = Column(String(255), nullable=False)

    source_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)), nullable=False)
    source = relationship('Node', foreign_keys=[source_id],
                          backref=backref('out_edges', lazy='dynamic', cascade='all, delete-orphan'))

    target_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)), nullable=False)
    target = relationship('Node', foreign_keys=[target_id],
                          backref=backref('in_edges', lazy='dynamic', cascade='all, delete-orphan'))

    evidence_id = Column(Integer, ForeignKey('{}.id'.format(EVIDENCE_TABLE_NAME)), nullable=True)
    evidence = relationship("Evidence", backref=backref('edges', lazy='dynamic'))

    annotations = relationship('AnnotationEntry', secondary=edge_annotation, lazy="dynamic",
                               backref=backref('edges', lazy='dynamic'))
    properties = relationship('Property', secondary=edge_property, lazy="dynamic")  # , cascade='all, delete-orphan')

    sha512 = Column(String(255), index=True, doc='The hash of the source, target, and associated metadata')

    def __str__(self):
        return self.bel

    def __repr__(self):
        return '<Edge {}: {}>'.format(self.sha512[:10], self.bel)

    def get_annotations_json(self):
        """Formats the annotations properly

        :rtype: Optional[dict[str,dict[str,bool]]
        """
        annotations = {}

        for entry in self.annotations:
            if entry.annotation.keyword not in annotations:
                annotations[entry.annotation.keyword] = {entry.name: True}
            else:
                annotations[entry.annotation.keyword][entry.name] = True

        return annotations or None

    def get_data_json(self):
        """Gets the PyBEL edge data dictionary this edge represents

        :rtype: dict
        """
        data = {
            RELATION: self.relation,
        }

        annotations = self.get_annotations_json()
        if annotations:
            data[ANNOTATIONS] = annotations

        if self.evidence:
            data.update(self.evidence.to_json())

        for prop in self.properties:  # FIXME this is also probably broken for translocations or mixed activity/degrad
            if prop.side not in data:
                data[prop.side] = prop.to_json()
            else:
                data[prop.side].update(prop.to_json())

        return data

    def to_json(self, include_id=False, include_hash=False):
        """Creates a dictionary of one BEL Edge that can be used to create an edge in a :class:`BELGraph`.

        :param bool include_id: Include the database identifier?
        :param bool include_hash: Include the node hash?
        :return: Dictionary that contains information about an edge of a :class:`BELGraph`. Including participants
                 and edge data information.
        :rtype: dict
        """
        result = {
            'source': self.source.to_json(),
            'target': self.target.to_json(),
            'data': self.get_data_json(),
        }

        if include_id:
            result['id'] = self.id

        if include_hash:
            result[HASH] = self.sha512

        return result

    def insert_into_graph(self, graph):
        """Inserts this edge into a BEL Graph

        :param pybel.BELGraph graph: A BEL graph
        """
        u = graph.add_node_from_data(self.source.to_json())
        v = graph.add_node_from_data(self.target.to_json())

        graph.add_edge(u, v, attr_dict=self.get_data_json())


class Property(Base):
    """The property table contains additional information that is used to describe the context of a relation."""
    __tablename__ = PROPERTY_TABLE_NAME

    id = Column(Integer, primary_key=True)

    is_subject = Column(Boolean, doc='Identifies which participant of the edge if affected by the given property')
    modifier = Column(String(255), doc='The modifier: one of activity, degradation, location, or translocation')

    relative_key = Column(String(255), nullable=True, doc='Relative key of effect e.g. to_tloc or from_tloc')

    sha512 = Column(String(255), index=True)

    effect_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_ENTRY_TABLE_NAME)), nullable=True)
    effect = relationship('NamespaceEntry')

    @property
    def side(self):
        """Returns either :data:`pybel.constants.SUBJECT` or :data:`pybel.constants.OBJECT`

        :rtype: str
        """
        return SUBJECT if self.is_subject else OBJECT

    def to_json(self):
        """Creates a property dict that is used to recreate an edge dictionary for a :class:`BELGraph`.

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
