# -*- coding: utf-8 -*-

"""The query manager for the database."""

import datetime
from collections import Iterable

from six import string_types
from sqlalchemy import and_, func, or_

from .lookup_manager import LookupManager
from .models import Annotation, AnnotationEntry, Author, Citation, Edge, Evidence, Namespace, NamespaceEntry, Node
from ..constants import CITATION_TYPE_PUBMED
from ..struct import BELGraph
from ..utils import hash_node, parse_datetime

__all__ = [
    'QueryManager',
]


def graph_from_edges(edges, **kwargs):
    """Build a BEL graph from edges.

    :param iter[Edge] edges: An iterable of edges from the database
    :param kwargs: Arguments to pass to :class:`pybel.BELGraph`
    :rtype: BELGraph
    """
    graph = BELGraph(**kwargs)

    for edge in edges:
        edge.insert_into_graph(graph)

    return graph


class QueryManager(LookupManager):
    """An extension to the Manager to make queries over the database."""

    def count_nodes(self):
        """Count the number of nodes in the database.

        :rtype: int
        """
        return self.session.query(func.count(Node.id)).scalar()

    def get_node_tuple_by_hash(self, node_hash):
        """Looks up a node by the hash and returns the corresponding PyBEL node tuple

        :param str node_hash: The hash of a PyBEL node tuple from :func:`pybel.utils.hash_node`
        :rtype: Optional[tuple]
        """
        node = self.get_node_by_hash(node_hash)

        if node is None:
            return

        return node.to_tuple()

    def get_node_by_tuple(self, node):
        """Looks up a node by the PyBEL node tuple

        :param tuple node: A PyBEL node tuple
        :rtype: Optional[Node]
        """
        node_hash = hash_node(node)
        return self.get_node_by_hash(node_hash)

    def query_nodes(self, bel=None, type=None, namespace=None, name=None):
        """Query nodes in the database.

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
        """Count the number of edges in the database.

        :rtype: int
        """
        return self.session.query(func.count(Edge.id)).scalar()

    def get_edges_with_citation(self, citation):
        """Get the edges with the given citation.

        :param Citation citation:
        :rtype: iter[Edge]
        """
        return self.session.query(Edge).join(Evidence).filter(Evidence.citation == citation)

    def get_edges_with_citations(self, citations):
        """Get edges with one of the given citations.

        :param iter[Citation] citations:
        :rtype: list[Edge]
        """
        return self.session.query(Edge).join(Evidence).filter(Evidence.citation.in_(citations)).all()

    def search_edges_with_evidence(self, evidence):
        """Searches edges with the given evidence

        :param str evidence: A string to search evidences. Can use wildcard percent symbol (%).
        :rtype: list[Edge]
        """
        return self.session.query(Edge).join(Evidence).filter(Evidence.text.like(evidence)).all()

    def search_edges_with_bel(self, bel):
        """Searches edges with given BEL

        :param str bel: A BEL string to use as a search
        :rtype: list[Edge]
        """
        return self.session.query(Edge).filter(Edge.bel.like(bel)).all()

    def get_edges_with_annotation(self, annotation, value):
        """

        :param str annotation:
        :param str value:
        :rtype: list[Edge]
        """
        query = self.session.query(Edge).join(AnnotationEntry, Edge.annotations).join(Annotation)
        query = query.filter(Annotation.keyword == annotation).filter(AnnotationEntry.name == value)
        return query.all()

    @staticmethod
    def _add_edge_function_filter(query, edge_node_id, node_type):
        """See usage in self.query_edges."""
        return query.join(Node, edge_node_id == Node.id).filter(Node.type == node_type)

    def query_edges(self, bel=None, source_function=None, source=None, target_function=None, target=None,
                    relation=None):
        """Query edges in the database.

        :param str bel: BEL statement that represents the desired edge.
        :param str source_function: Filter source nodes with the given BEL function
        :param source: BEL term of source node e.g. ``p(HGNC:APP)`` or :class:`Node` object.
        :type source: str or Node
        :param str target_function: Filter target nodes with the given BEL function
        :param target: BEL term of target node e.g. ``p(HGNC:APP)`` or :class:`Node` object.
        :type target: str or Node
        :param str relation: The relation that should be present between source and target node.
        :rtype: list[Edge]
        """
        if bel:
            return self.search_edges_with_bel(bel)

        query = self.session.query(Edge)

        if relation:
            query = query.filter(Edge.relation.like(relation))

        if source_function:
            query = self._add_edge_function_filter(query, Edge.source_id, source_function)

        if target_function:
            query = self._add_edge_function_filter(query, Edge.target_id, target_function)

        if source:
            if isinstance(source, string_types):
                source = self.query_nodes(bel=source)
                if len(source) == 0:
                    return []
                source = source[0]  # FIXME what if this matches multiple?
                query = query.filter(Edge.source == source)
            elif isinstance(source, Node):
                query = query.filter(Edge.source == source)
            else:
                raise TypeError('Invalid type of {}: {}'.format(source, source.__class__.__name__))

        if target:
            if isinstance(target, string_types):
                targets = self.query_nodes(bel=target)
                target = targets[0]  # FIXME what if this matches multiple?
                query = query.filter(Edge.target == target)
            elif isinstance(target, Node):
                query = query.filter(Edge.target == target)
            else:
                raise TypeError('Invalid type of {}: {}'.format(target, target.__class__.__name__))

        return query.all()

    def query_citations(self, type=None, reference=None, name=None, author=None, date=None, evidence_text=None):
        """Query citations in the database.

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

    def query_edges_by_pubmed_identifiers(self, pubmed_identifiers):
        """Get all edges annotated to the documents identified by the given PubMed identifiers.

        :param list[str] pubmed_identifiers: A list of PubMed document identifiers
        :rtype: list[Edge]
        """
        fi = and_(Citation.type == CITATION_TYPE_PUBMED, Citation.reference.in_(pubmed_identifiers))
        return self.session.query(Edge).join(Evidence).join(Citation).filter(fi).all()

    @staticmethod
    def _edge_both_nodes(nodes):
        """Get edges where both the source and target are in the list of nodes.

        :param list[Node] nodes: A list of node identifiers
        """
        node_ids = [node.id for node in nodes]

        return and_(
            Edge.source_id.in_(node_ids),
            Edge.target_id.in_(node_ids),
        )

    def query_induction(self, nodes):
        """Get all edges between any of the given nodes.

        :param list[Node] nodes: A list of nodes (length > 2)
        :rtype: list[Edge]
        """
        if len(nodes) < 2:
            raise ValueError('not enough nodes given to induce over')

        return self.session.query(Edge).filter(self._edge_both_nodes(nodes)).all()

    @staticmethod
    def _edge_one_node(nodes):
        """Get edges where either the source or target are in the list of nodes.

        :param list[Node] nodes: A list of node identifiers

        Note: doing this with the nodes directly is not yet supported by SQLAlchemy

        .. code-block:: python

            return or_(
                Edge.source.in_(nodes),
                Edge.target.in_(nodes),
            )
        """
        node_ids = [node.id for node in nodes]

        return or_(
            Edge.source_id.in_(node_ids),
            Edge.target_id.in_(node_ids),
        )

    def query_neighbors(self, nodes):
        """Get all edges incident to any of the given nodes.

        :param list[Node] nodes: A list of nodes
        :rtype: list[Edge]
        """
        return self.session.query(Edge).filter(self._edge_one_node(nodes)).all()
