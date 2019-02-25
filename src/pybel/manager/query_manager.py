# -*- coding: utf-8 -*-

"""The query manager for the database."""

import datetime
from typing import Iterable, List, Optional, Union

from sqlalchemy import and_, or_

from .lookup_manager import LookupManager
from .models import Author, Citation, Edge, Evidence, Namespace, NamespaceEntry, Node
from ..constants import CITATION_TYPE_PUBMED
from ..struct import BELGraph
from ..utils import parse_datetime

__all__ = [
    'QueryManager',
    'graph_from_edges',
]


def graph_from_edges(edges: Iterable[Edge], **kwargs) -> BELGraph:
    """Build a BEL graph from edges."""
    graph = BELGraph(**kwargs)

    for edge in edges:
        edge.insert_into_graph(graph)

    return graph


class QueryManager(LookupManager):
    """An extension to the Manager to make queries over the database."""

    def count_nodes(self) -> int:
        """Count the number of nodes in the database."""
        return self._count_model(Node)

    def query_nodes(self,
                    bel: Optional[str] = None,
                    type: Optional[str] = None,
                    namespace: Optional[str] = None,
                    name: Optional[str] = None,
                    ) -> List[Node]:
        """Query nodes in the database.

        :param bel: BEL term that describes the biological entity. e.g. ``p(HGNC:APP)``
        :param type: Type of the biological entity. e.g. Protein
        :param namespace: Namespace keyword that is used in BEL. e.g. HGNC
        :param name: Name of the biological entity. e.g. APP
        """
        q = self.session.query(Node)

        if bel:
            q = q.filter(Node.bel.contains(bel))

        if type:
            q = q.filter(Node.type == type)

        if namespace or name:
            q = q.join(NamespaceEntry)

            if namespace:
                q = q.join(Namespace).filter(Namespace.keyword.contains(namespace))

            if name:
                q = q.filter(NamespaceEntry.name.contains(name))

        return q

    def count_edges(self) -> int:
        """Count the number of edges in the database."""
        return self._count_model(Edge)

    def get_edges_with_citation(self, citation: Citation) -> List[Edge]:
        """Get the edges with the given citation."""
        return self.session.query(Edge).join(Evidence).filter(Evidence.citation == citation)

    def get_edges_with_citations(self, citations: Iterable[Citation]) -> List[Edge]:
        """Get edges with one of the given citations."""
        return self.session.query(Edge).join(Evidence).filter(Evidence.citation.in_(citations)).all()

    def search_edges_with_evidence(self, evidence: str) -> List[Edge]:
        """Search edges with the given evidence.

        :param evidence: A string to search evidences. Can use wildcard percent symbol (%).
        """
        return self.session.query(Edge).join(Evidence).filter(Evidence.text.like(evidence)).all()

    def search_edges_with_bel(self, bel: str) -> List[Edge]:
        """Search edges with given BEL.

        :param bel: A BEL string to use as a search
        """
        return self.session.query(Edge).filter(Edge.bel.like(bel))

    def get_edges_with_annotation(self, annotation: str, value: str) -> List[Edge]:
        """Search edges with the given annotation/value pair."""
        query = self.session.query(Edge).join(NamespaceEntry, Edge.annotations).join(Namespace)
        query = query.filter(Namespace.keyword == annotation).filter(NamespaceEntry.name == value)
        return query.all()

    @staticmethod
    def _add_edge_function_filter(query, edge_node_id, node_type):
        """See usage in self.query_edges."""
        return query.join(Node, edge_node_id == Node.id).filter(Node.type == node_type)

    def query_edges(self,
                    bel: Optional[str] = None,
                    source_function: Optional[str] = None,
                    source: Union[None, str, Node] = None,
                    target_function: Optional[str] = None,
                    target: Union[None, str, Node] = None,
                    relation: Optional[str] = None,
                    ):
        """Return a query over the edges in the database.

        Usually this means that you should call ``list()`` or ``.all()`` on this result.

        :param bel: BEL statement that represents the desired edge.
        :param source_function: Filter source nodes with the given BEL function
        :param source: BEL term of source node e.g. ``p(HGNC:APP)`` or :class:`Node` object.
        :param target_function: Filter target nodes with the given BEL function
        :param target: BEL term of target node e.g. ``p(HGNC:APP)`` or :class:`Node` object.
        :param relation: The relation that should be present between source and target node.
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
            if isinstance(source, str):
                source = self.query_nodes(bel=source)
                if source.count() == 0:
                    return []
                source = source.first()  # FIXME what if this matches multiple?
                query = query.filter(Edge.source == source)
            elif isinstance(source, Node):
                query = query.filter(Edge.source == source)
            else:
                raise TypeError('Invalid type of {}: {}'.format(source, source.__class__.__name__))

        if target:
            if isinstance(target, str):
                targets = self.query_nodes(bel=target).all()
                target = targets[0]  # FIXME what if this matches multiple?
                query = query.filter(Edge.target == target)
            elif isinstance(target, Node):
                query = query.filter(Edge.target == target)
            else:
                raise TypeError('Invalid type of {}: {}'.format(target, target.__class__.__name__))

        return query

    def query_citations(self,
                        type: Optional[str] = None,
                        reference: Optional[str] = None,
                        name: Optional[str] = None,
                        author: Union[None, str, List[str]] = None,
                        date: Union[None, str, datetime.date] = None,
                        evidence_text: Optional[str] = None,
                        ) -> List[Citation]:
        """Query citations in the database.

        :param type: Type of the citation. e.g. PubMed
        :param reference: The identifier used for the citation. e.g. PubMed_ID
        :param name: Title of the citation.
        :param author: The name or a list of names of authors participated in the citation.
        :param date: Publishing date of the citation.
        :param evidence_text:
        """
        query = self.session.query(Citation)

        if author is not None:
            query = query.join(Author, Citation.authors)
            if isinstance(author, str):
                query = query.filter(Author.name.like(author))
            elif isinstance(author, Iterable):
                query = query.filter(Author.has_name_in(set(author)))
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
            elif isinstance(date, str):
                query = query.filter(Citation.date == parse_datetime(date))

        if evidence_text:
            query = query.join(Evidence).filter(Evidence.text.like(evidence_text))

        return query.all()

    def query_edges_by_pubmed_identifiers(self, pubmed_identifiers: List[str]) -> List[Edge]:
        """Get all edges annotated to the documents identified by the given PubMed identifiers."""
        fi = and_(Citation.type == CITATION_TYPE_PUBMED, Citation.reference.in_(pubmed_identifiers))
        return self.session.query(Edge).join(Evidence).join(Citation).filter(fi).all()

    @staticmethod
    def _edge_both_nodes(nodes: List[Node]):
        """Get edges where both the source and target are in the list of nodes."""
        node_ids = [node.id for node in nodes]

        return and_(
            Edge.source_id.in_(node_ids),
            Edge.target_id.in_(node_ids),
        )

    def query_induction(self, nodes: List[Node]) -> List[Edge]:
        """Get all edges between any of the given nodes (minimum length of 2)."""
        if len(nodes) < 2:
            raise ValueError('not enough nodes given to induce over')

        return self.session.query(Edge).filter(self._edge_both_nodes(nodes)).all()

    @staticmethod
    def _edge_one_node(nodes: List[Node]):
        """Get edges where either the source or target are in the list of nodes.

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

    def query_neighbors(self, nodes: List[Node]) -> List[Edge]:
        """Get all edges incident to any of the given nodes."""
        return self.session.query(Edge).filter(self._edge_one_node(nodes)).all()
