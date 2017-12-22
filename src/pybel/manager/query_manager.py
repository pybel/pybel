# -*- coding: utf-8 -*-

import datetime
from collections import Iterable

from six import string_types
from sqlalchemy import and_, func, or_

from .lookup_manager import LookupManager
from .models import (
    Annotation, AnnotationEntry, Author, Citation, Edge, Evidence, Namespace,
    NamespaceEntry, Node, Property,
)
from ..constants import *
from ..struct import BELGraph
from ..utils import hash_node, parse_datetime

__all__ = [
    'QueryManager'
]


def graph_from_edges(edges, **kwargs):
    """Builds a BEL graph from edges

    :param iter[Edge] edges: An iterable of edges from the database
    :param kwargs: Arguments to pass to :class:`pybel.BELGraph`
    :rtype: BELGraph
    """
    graph = BELGraph(**kwargs)

    for edge in edges:
        edge.insert_into_graph(graph)

    return graph


class QueryManager(LookupManager):
    """Groups queries over the edge store"""

    def count_nodes(self):
        """Counts the number of nodes in the cache

        :rtype: int
        """
        return self.session.query(func.count(Node.id)).scalar()

    def get_node_tuple_by_hash(self, node_hash):
        """Looks up a node by the hash and returns the corresponding PyBEL node tuple

        :param str node_hash: The hash of a PyBEL node tuple from :func:`pybel.utils.hash_node`
        :rtype: tuple
        """
        node = self.get_node_by_hash(node_hash)
        return node.to_tuple()

    def get_node_by_tuple(self, node):
        """Looks up a node by the PyBEL node tuple

        :param tuple node: A PyBEL node tuple
        :rtype: Node
        """
        node_hash = hash_node(node)
        return self.get_node_by_hash(node_hash)

    def query_nodes(self, bel=None, type=None, namespace=None, name=None):
        """Builds and runs a query over all nodes in the PyBEL cache.

        :param str bel: BEL term that describes the biological entity. e.g. ``p(HGNC:APP)``
        :param str type: Type of the biological entity. e.g. Protein
        :param str namespace: Namespace keyword that is used in BEL. e.g. HGNC
        :param str name: Name of the biological entity. e.g. APP
        :rtype: list[Node]
        """
        q = self.session.query(Node)

        if bel:
            q = q.filter(Node.bel.like(bel))

        if type:
            q = q.filter(Node.type.like(type))

        if namespace or name:
            q = q.join(NamespaceEntry)

            if namespace:
                q = q.join(Namespace).filter(Namespace.keyword.like(namespace))

            if name:
                q = q.filter(NamespaceEntry.name.like(name))

        return q.all()

    def count_edges(self):
        """Counts the number of edges in the cache

        :rtype: int
        """
        return self.session.query(func.count(Edge.id)).scalar()

    def query_edges(self, bel=None, source=None, target=None, relation=None, citation=None, evidence=None,
                    annotation=None, property=None):
        """Builds and runs a query over all edges in the PyBEL cache.

        :param str bel: BEL statement that represents the desired edge.
        :param str or Node source: BEL term of source node e.g. ``p(HGNC:APP)`` or :class:`Node` object.
        :param str or Node target: BEL term of target node e.g. ``p(HGNC:APP)`` or :class:`Node` object.
        :param str relation: The relation that should be present between source and target node.
        :param str or Citation citation: The citation that backs the edge up. It is possible to use the reference_id
                         or a Citation object.
        :param str or Evidence evidence: The supporting text of the edge
        :param dict or str annotation: Dictionary of {annotationKey: annotationValue} parameters or just an
                                        annotationValue parameter as string.
        :param property: An edge property object or a corresponding database identifier.
        :rtype: list[Edge]
        """
        query = self.session.query(Edge)

        if bel:
            query = query.filter(Edge.bel.like(bel))

        if relation:
            query = query.filter(Edge.relation.like(relation))

        if annotation:
            query = query.join(AnnotationEntry, Edge.annotations)
            if isinstance(annotation, dict):
                query = query.join(Annotation).filter(Annotation.keyword.in_(list(annotation.keys())))
                query = query.filter(AnnotationEntry.name.in_(list(annotation.values())))

            elif isinstance(annotation, string_types):
                query = query.filter(AnnotationEntry.name.like(annotation))

        if source:
            if isinstance(source, string_types):
                source = self.query_nodes(bel=source)
                if len(source) == 0:
                    return []
                source = source[0]  # FIXME what if this matches multiple?

            query = query.filter(Edge.source == source)

        if target:
            if isinstance(target, string_types):
                targets = self.query_nodes(bel=target)
                target = targets[0]  # FIXME what if this matches multiple?

            query = query.filter(Edge.target == target)

        if citation or evidence:
            query = query.join(Evidence)

            if citation:
                if isinstance(citation, Citation):
                    query = query.filter(Evidence.citation == citation)

                elif isinstance(citation, list) and isinstance(citation[0], Citation):
                    query = query.filter(Evidence.citation.in_(citation))

                elif isinstance(citation, string_types):
                    query = query.join(Citation).filter(Citation.reference.like(citation))

            if evidence:
                if isinstance(evidence, Evidence):
                    query = query.filter(Edge.evidence == evidence)

                elif isinstance(evidence, string_types):
                    query = query.filter(Evidence.text.like(evidence))

        if property:
            query = query.join(Property, Edge.properties)

            if isinstance(property, Property):
                query = query.filter(Property.id == property.id)
            elif isinstance(property, int):
                query = query.filter(Property.id == property)

        return query.all()

    def query_citations(self, type=None, reference=None, name=None, author=None, date=None, evidence_text=None):
        """Builds and runs a query over all citations in the PyBEL cache.

        :param str type: Type of the citation. e.g. PubMed
        :param str reference: The identifier used for the citation. e.g. PubMed_ID
        :param str name: Title of the citation.
        :param str or list[str] author: The name or a list of names of authors participated in the citation.
        :param date: Publishing date of the citation.
        :type date: str or datetime.date
        :param str evidence_text:
        :rtype: list[Citation]
        """
        query = self.session.query(Citation)

        if author is not None:
            query = query.join(Author, Citation.authors)
            if isinstance(author, string_types):
                query = query.filter(Author.name.like(author))
            elif isinstance(author, Iterable):
                query = query.filter(Author.name.in_(set(author)))
            else:
                raise TypeError

        if type and not reference:
            query = query.filter(Citation.type.like(type))
        elif reference and type:
            query = query.filter(Citation.reference == reference)
        elif reference and not type:
            raise ValueError('reference specified without type')

        if name:
            query = query.filter(Citation.name.like(name))

        if date:
            if isinstance(date, datetime.date):
                query = query.filter(Citation.date == date)
            elif isinstance(date, string_types):
                query = query.filter(Citation.date == parse_datetime(date))

        if evidence_text:
            query = query.join(Evidence).filter(Evidence.text.like(evidence_text))

        return query.all()

    def query_edges_by_pmid(self, pubmed_identifiers):
        """Gets all edges annotated to the given documents

        :param list[str] pubmed_identifiers: A list of PubMed document identifiers
        :rtype: list[Edge]
        """
        return self.session.query(Edge) \
            .join(Evidence).join(Citation) \
            .filter(Citation.type == CITATION_TYPE_PUBMED,
                    Citation.reference.in_(pubmed_identifiers)).all()

    def query_induction(self, nodes):
        """Gets all edges between any of the given nodes

        :param list[Node] nodes: A list of nodes (length > 2)
        :rtype: list[Edge]
        """
        if len(nodes) < 2:
            raise ValueError('not enough nodes given to induce over')

        node_ids = [node.id for node in nodes]

        return self.session.query(Edge).filter(and_(Edge.source_id.in_(node_ids),
                                                    Edge.target_id.in_(node_ids))).all()

    def query_neighbors(self, nodes):
        """Gets all edges incident to any of the given nodes

        :param list[Node] nodes: A list of nodes
        :rtype: list[Edge]
        """
        node_ids = [node.id for node in nodes]
        return self.session.query(Edge).filter(or_(Edge.source_id.in_(node_ids),
                                                   Edge.target_id.in_(node_ids))).all()
