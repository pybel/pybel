# -*- coding: utf-8 -*-

"""This module contains the SQLAlchemy database models that support the definition cache and graph cache."""

import datetime

from sqlalchemy import (
    Boolean, Column, DDL, Date, DateTime, ForeignKey, Integer, LargeBinary, String, Table, Text,
    UniqueConstraint, event,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship

from .utils import int_or_str
from ..constants import *
from ..io.gpickle import from_bytes, to_bytes
from ..parser.canonicalize import node_to_tuple, sort_dict_list, sort_variant_dict_list

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


def reset_tables(engine):
    """Drops all tables in database"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def build_orphan_trigger(trigger_name, trigger_tablename, orphan_tablename, reference_tablename, reference_column,
                         orphan_column='id', trigger_time='AFTER', trigger_action='DELETE'):
    """builds a trigger to delete orphans in many-to-many relationships after deletion of a table.

    :param str trigger_name: Name that will be used to create the trigger in the database.
    :param str trigger_tablename: Name of the table that starts the trigger after deletion.
    :param str orphan_tablename: Name of the table that may contain orphan entries.
    :param str reference_tablename: Name of the table that should be used as reference to weather delete or not.
    :param str reference_column: Column in the reference table that should be checked.
    :param str orphan_column: Column in the orphan table that should be checked agains the reference table.
    :param str trigger_time: Timepoint the trigger gets called.
    :param str trigger_action: Action that calls the trigger.
    :return: :class:`DDL` object.
    """
    ddl = DDL('''
    CREATE TRIGGER {trigger_name} {trigger_time} {trigger_action} ON {trigger_tablename}
    FOR EACH ROW
    BEGIN
    DELETE FROM {orphan_tablename}
    WHERE {orphan_column} NOT IN (
        SELECT DISTINCT {reference_column}
        FROM {reference_tablename}
    );
    END;'''.format(
        trigger_name=trigger_name,
        trigger_time=trigger_time,
        trigger_action=trigger_action,
        trigger_tablename=trigger_tablename,
        orphan_tablename=orphan_tablename,
        orphan_column=orphan_column,
        reference_column=reference_column,
        reference_tablename=reference_tablename)
    )

    return ddl


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
    url = Column(String(255), nullable=False, unique=True, index=True,
                 doc='Source url of the given namespace definition file (.belns)')

    keyword = Column(String(8), index=True, doc='Keyword that is used in a BEL file to identify a specific namespace')
    name = Column(String(255), doc='Name of the given namespace')
    domain = Column(String(255), doc='Domain for which this namespace is valid')
    species = Column(String(255), nullable=True, doc='Taxonomy identifiers for which this namespace is valid')
    description = Column(Text, nullable=True, doc='Optional short description of the namespace')
    version = Column(String(255), nullable=True, doc='Version of the namespace')
    created = Column(DateTime, doc='DateTime of the creation of the namespace definition file')
    query_url = Column(Text, nullable=True, doc='URL that can be used to query the namespace (eternally from PyBEL)')

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

    def to_json(self, include_id=True):
        """Returns the table entry as a dictionary without the SQLAlchemy instance information.

        :rtype: dict
        """
        result = {
            'uploaded': self.uploaded,
            'url': self.url,
            'keyword': self.keyword,
            'name': self.name,
            'domain': self.domain,
            'species': self.species,
            'description': self.description,
            'version': self.version,
            'created': self.created,
            'query_url': self.query_url,
            'author': self.author,
            'license': self.license,
            'contact': self.contact,
            'citation': self.citation,
            'citation_description': self.citation_description,
            'citation_version': self.citation_version,
            'citation_published': self.citation_published,
            'citation_url': self.citation_url,
            'has_equivalences': self.has_equivalences
        }

        if include_id:
            result['id'] = self.id

        return result


class NamespaceEntry(Base):
    """Represents a name within a BEL namespace"""
    __tablename__ = NAMESPACE_ENTRY_TABLE_NAME

    id = Column(Integer, primary_key=True)

    name = Column(Text, nullable=False, doc='Name that is defined in the corresponding namespace definition file')
    encoding = Column(String(8), nullable=True, doc='The biological entity types for which this name is valid')

    namespace_id = Column(Integer, ForeignKey(NAMESPACE_TABLE_NAME + '.id'), nullable=False, index=True)
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
        return '{}:{}'.format(self.namespace.url, self.name)

    def to_json(self, include_id=False):
        """Describes the namespaceEntry as dictionary of Namespace-Keyword and Name.

        :rtype: dict
        """
        result = {
            NAMESPACE: self.namespace.keyword,
            NAME: self.name
        }

        if include_id:
            result[ID] = self.id

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

    def get_entries(self):
        """Gets a set of the names of all etries

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

        :rtype: dict
        """
        result = {
            'uploaded': self.uploaded,
            'url': self.url,
            'keyword': self.keyword,
            'type': self.type,
            'description': self.description,
            'usage': self.usage,
            'version': self.version,
            'created': self.created,
            'name': self.name,
            'author': self.author,
            'license': self.license,
            'contact': self.contact,
            'citation': self.citation,
            'citation_description': self.citation_description,
            'citation_version': self.citation_version,
            'citation_published': self.citation_published,
            'citation_url': self.citation_url
        }

        if include_id:
            result[ID] = self.id

        return result

    def __str__(self):
        return self.keyword


class AnnotationEntry(Base):
    """Represents a value within a BEL Annotation"""
    __tablename__ = ANNOTATION_ENTRY_TABLE_NAME

    id = Column(Integer, primary_key=True)

    name = Column(String(255), nullable=False,
                  doc='Name that is defined in the corresponding annotation definition file')
    label = Column(String(255), nullable=True)

    annotation_id = Column(Integer, ForeignKey('{}.id'.format(ANNOTATION_TABLE_NAME)), index=True)
    annotation = relationship('Annotation', backref=backref('entries', lazy='dynamic'))

    children = relationship(
        'AnnotationEntry',
        secondary=annotation_hierarchy,
        primaryjoin=id == annotation_hierarchy.c.left_id,
        secondaryjoin=id == annotation_hierarchy.c.right_id
    )

    def to_json(self, include_id=False):
        """Describes the annotationEntry as dictionary of Annotation-Keyword and Annotation-Name.

        :rtype: dict
        """
        result = {
            'annotation_keyword': self.annotation.keyword,
            'annotation': self.name
        }

        if include_id:
            result[ID] = self.id

        return result


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
    contact = Column(String(255), nullable=True, doc='Contact information extracted from the underlying BEL file')
    description = Column(Text, nullable=True, doc='Descriptive text extracted from the BEL file')
    copyright = Column(Text, nullable=True, doc='Copyright information')
    disclaimer = Column(String(255), nullable=True, doc='Disclaimer information')
    licenses = Column(String(255), nullable=True, doc='License information')

    created = Column(DateTime, default=datetime.datetime.utcnow)
    blob = Column(LargeBinary(LONGBLOB), doc='A pickled version of this network')

    nodes = relationship('Node', secondary=network_node, lazy="dynamic")  # backref='networks'
    edges = relationship('Edge', secondary=network_edge, lazy="dynamic")  # backref='networks'

    __table_args__ = (
        UniqueConstraint(name, version),
    )

    def to_json(self, include_id=False):
        """Returns this network as JSON

        :rtype: dict
        """
        result = {
            'created': self.created,
            METADATA_NAME: self.name,
            METADATA_VERSION: self.version,
        }

        if include_id:
            result[ID] = self.id

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

    def __repr__(self):
        return '{} v{}'.format(self.name, self.version)

    def __str__(self):
        return repr(self)

    def as_bel(self):
        """Gets this network and loads it into a :class:`BELGraph`

        :rtype: BELGraph
        """
        return from_bytes(self.blob)

    def store_bel(self, graph):
        """Inserts a bel graph

        :param BELGraph graph: A BEL Graph
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
    namespace_entry_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_ENTRY_TABLE_NAME)), nullable=True)
    namespace_entry = relationship('NamespaceEntry', foreign_keys=[namespace_entry_id])
    namespace_pattern = Column(String(255), nullable=True, doc="Contains regex pattern for value identification.")
    is_variant = Column(Boolean, default=False, doc='Identifies weather or not the given node is a variant')
    fusion = Column(Boolean, default=False, doc='Identifies weather or not the given node is a fusion')

    bel = Column(String(255), nullable=False, doc='Valid BEL term that represents the given node')

    sha512 = Column(String(255), index=True)

    modifications = relationship("Modification", secondary=node_modification, backref='nodes')

    def __str__(self):
        return self.bel

    def to_json(self, include_id=False):
        """Serializes this node as a PyBEL node data dictionary

        :param bool include_id: Include the database identifier?
        :rtype: dict
        """
        result = {
            FUNCTION: self.type,
        }

        if include_id:
            result[ID] = self.id

        if self.namespace_entry:
            namespace_entry = self.namespace_entry.to_json()
            result.update(namespace_entry)

        if self.is_variant:
            if self.fusion:
                mod = self.modifications[0].data
                result[FUSION] = mod['mod_data']
            else:
                result[VARIANTS] = sort_variant_dict_list(
                    modification.data['mod_data']
                    for modification in self.modifications
                )

        if self.type == REACTION:
            reactants = []
            products = []

            for edge in self.out_edges:
                if edge.relation == HAS_REACTANT:
                    reactants.append(edge.target.to_json())
                elif edge.relation == HAS_PRODUCT:
                    products.append(edge.target.to_json())

            result[REACTANTS] = sort_dict_list(reactants)
            result[PRODUCTS] = sort_dict_list(products)

        if self.type == COMPOSITE or (self.type == COMPLEX and not self.namespace_entry):
            result[MEMBERS] = sort_dict_list(
                edge.target.to_json()
                for edge in self.out_edges
                if edge.relation == HAS_COMPONENT
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

    modType = Column(String(255), doc='Type of the stored modification e.g. Fusion')
    variantString = Column(String(255), nullable=True)

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
    aminoA = Column(String(3), nullable=True, doc='Three letter amino acid code')
    position = Column(Integer, nullable=True, doc='Position')

    sha512 = Column(String(255), index=True)

    # TODO wreck this
    @property
    def data(self):
        """Recreates a is_variant dictionary for :class:`BELGraph`

        :return: Dictionary that describes a variant or a fusion.
        :rtype: dict
        """
        mod_dict = {}
        mod_key = []
        if self.modType == FUSION:
            mod_dict.update({
                PARTNER_3P: self.p3Partner.to_json(),
                PARTNER_5P: self.p5Partner.to_json(),
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
                    FUSION_START: int_or_str(self.p5Start),
                    FUSION_STOP: int_or_str(self.p5Stop),
                })
                mod_key.append((self.p5Reference, self.p5Start, self.p5Stop,))

            mod_key.append((mod_dict[PARTNER_3P][NAMESPACE], mod_dict[PARTNER_3P][NAME],))

            if self.p3Missing:
                mod_dict[RANGE_3P][FUSION_MISSING] = self.p3Missing
                mod_key.append((self.p3Missing,))

            else:
                mod_dict[RANGE_3P].update({
                    FUSION_REFERENCE: self.p3Reference,
                    FUSION_START: int_or_str(self.p3Start),
                    FUSION_STOP: int_or_str(self.p3Stop)
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
                        FRAGMENT_START: int_or_str(self.p3Start),
                        FRAGMENT_STOP: int_or_str(self.p3Stop)
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

    def to_json(self):
        """Enables json serialization for the class this method is defined in.

        :rtype: dict
        """
        return self.data['mod_key']


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

    def to_json(self, include_id=False):
        """Creates a citation dictionary that is used to recreate the edge data dictionary of a :class:`BELGraph`.

        :return: Citation dictionary for the recreation of a :class:`BELGraph`.
        :rtype: dict
        """
        result = {
            CITATION_REFERENCE: self.reference,
            CITATION_TYPE: self.type
        }

        if include_id:
            result[ID] = self.id

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
            result[CITATION_AUTHORS] = "|".join(sorted(
                author.name
                for author in self.authors
            ))

        return result


class Evidence(Base):
    """This table contains the evidence text that proves a specific relationship and refers the source that is cited."""
    __tablename__ = EVIDENCE_TABLE_NAME

    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False, doc='Supporting text from a given publication')

    citation_id = Column(Integer, ForeignKey('{}.id'.format(CITATION_TABLE_NAME)))
    citation = relationship('Citation', backref=backref('evidences'))

    sha512 = Column(String(255), index=True)

    def __str__(self):
        return '{}:{}'.format(self.citation, self.text)

    def to_json(self, include_id=False):
        """Creates a dictionary that is used to recreate the edge data dictionary for a :class:`BELGraph`.

        :return: Dictionary containing citation and evidence for a :class:`BELGraph` edge.
        :rtype: dict
        """
        result = {
            CITATION: self.citation.to_json(),
            EVIDENCE: self.text
        }

        if include_id:
            result[ID] = self.id

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
    source = relationship('Node', foreign_keys=[source_id], backref=backref('out_edges', lazy='dynamic'))

    target_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)), nullable=False)
    target = relationship('Node', foreign_keys=[target_id], backref=backref('in_edges', lazy='dynamic'))

    evidence_id = Column(Integer, ForeignKey('{}.id'.format(EVIDENCE_TABLE_NAME)), nullable=True)
    evidence = relationship("Evidence")

    annotations = relationship('AnnotationEntry', secondary=edge_annotation, lazy="dynamic")  # , backref='edges'
    properties = relationship('Property', secondary=edge_property, lazy="dynamic")  # , cascade='all, delete-orphan')
    networks = relationship('Network', secondary=network_edge, lazy="dynamic")

    sha512 = Column(String(255), index=True)

    def __str__(self):
        return self.bel

    def get_data_json(self):
        """Gets the PyBEL edge data dictionary this edge represents

        :rtype: dict
        """
        data = {
            RELATION: self.relation,
            ANNOTATIONS: {
                entry.annotation.keyword: entry.name
                for entry in self.annotations
            }
        }

        if self.evidence:
            data.update(self.evidence.to_json())

        for prop in self.properties:
            prop_info = prop.data
            prop_info_data = prop_info['data']

            if prop_info['participant'] in data:  # TODO reinvestigate this
                data[prop_info['participant']].update(prop_info_data)
            else:
                data.update(prop_info_data)

        return data

    def to_json(self, include_id=False):
        """Creates a dictionary of one BEL Edge that can be used to create an edge in a :class:`BELGraph`.

        :return: Dictionary that contains information about an edge of a :class:`BELGraph`. Including participants
                 and edge data information.
        :rtype: dict
        """
        result = {
            'source': self.source.to_json(),
            'target': self.target.to_json(),
            'data': self.get_data_json()
        }

        if include_id:
            result[ID] = self.id

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

    # TODO refactor participant to be a boolean, for_subject, since it can only be SUBJECT or OBJECT
    participant = Column(String(255), doc='Identifies which participant of the edge if affected by the given property')
    modifier = Column(String(255), doc='The modifier to the corresponding participant')
    relativeKey = Column(String(255), nullable=True, doc='Relative key of effect e.g. to_tloc or from_tloc')
    propValue = Column(String(255), nullable=True, doc='Value of the effect')
    sha512 = Column(String(255), index=True)

    # TODO refactor effect to reference NamespaceEntry
    effectNamespace = Column(String(255), nullable=True, doc='Optional namespace that defines modifier value')
    effectName = Column(String(255), nullable=True, doc='Value for specific modifiers e.g. Activity')

    namespaceEntry_id = Column(Integer, ForeignKey('{}.id'.format(NAMESPACE_ENTRY_TABLE_NAME)), nullable=True)
    namespaceEntry = relationship('NamespaceEntry')

    @property
    def data(self):
        """Creates a property dict that is used to recreate an edge dictionary for a :class:`BELGraph`.

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

        if self.modifier == LOCATION:
            prop_dict['data'][self.participant] = {
                LOCATION: self.namespaceEntry.to_json()
            }

        if self.relativeKey:
            prop_dict['data'][self.participant][EFFECT] = {
                self.relativeKey: self.propValue if self.propValue else self.namespaceEntry.to_json()
            }
        elif self.effectNamespace:
            prop_dict['data'][self.participant][EFFECT] = {  # TODO reference NamespaceEntry dictionary?
                NAMESPACE: self.effectNamespace,
                NAME: self.effectName
            }

        return prop_dict

    def to_json(self):
        """Enables json serialization for the class this method is defined in.

        :rtype: dict
        """
        return self.data['data']


trigger_drop_orphan_edge_annotation_relations = build_orphan_trigger(
    trigger_name='drop_orphan_edge_annotation_relations',
    trigger_tablename=NETWORK_TABLE_NAME,
    # PROPERTY_TABLE_NAME,
    orphan_tablename=EDGE_ANNOTATION_TABLE_NAME,
    reference_tablename=NETWORK_EDGE_TABLE_NAME,
    reference_column='edge_id',
    orphan_column='edge_id'
)
event.listen(Network.__table__, 'after_create', trigger_drop_orphan_edge_annotation_relations)

trigger_drop_orphan_edge_property_relations = build_orphan_trigger(
    trigger_name='drop_orphan_edge_property_relations',
    trigger_tablename=EDGE_ANNOTATION_TABLE_NAME,
    orphan_tablename=EDGE_PROPERTY_TABLE_NAME,
    reference_tablename=NETWORK_EDGE_TABLE_NAME,
    reference_column='edge_id',
    orphan_column='edge_id'
)
event.listen(edge_annotation, 'after_create', trigger_drop_orphan_edge_property_relations)

trigger_drop_orphan_properties = build_orphan_trigger(
    trigger_name='drop_orphan_properties',
    trigger_tablename=EDGE_PROPERTY_TABLE_NAME,
    orphan_tablename=PROPERTY_TABLE_NAME,
    reference_tablename=EDGE_PROPERTY_TABLE_NAME,
    reference_column='property_id'
)
event.listen(edge_property, 'after_create', trigger_drop_orphan_properties)

trigger_drop_orphan_edges = build_orphan_trigger(
    trigger_name='drop_orphan_edges',
    trigger_tablename=PROPERTY_TABLE_NAME,
    orphan_tablename=EDGE_TABLE_NAME,
    reference_tablename=NETWORK_EDGE_TABLE_NAME,
    reference_column='edge_id'
)
event.listen(Property.__table__, 'after_create', trigger_drop_orphan_edges)

trigger_drop_orphan_modifications = build_orphan_trigger(
    trigger_name='drop_orphan_modifications',
    trigger_tablename=NODE_TABLE_NAME,
    orphan_tablename=MODIFICATION_TABLE_NAME,
    reference_tablename=NODE_MODIFICATION_TABLE_NAME,
    reference_column='modification_id'
)
event.listen(Node.__table__, 'after_create', trigger_drop_orphan_modifications)
