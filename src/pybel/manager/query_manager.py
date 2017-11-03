# -*- coding: utf-8 -*-

import datetime

from sqlalchemy import and_, func, or_

from .lookup_manager import LookupManager
from .models import (
    Annotation, AnnotationEntry, Author, Citation, Edge, Evidence, Modification, Namespace,
    NamespaceEntry, Node, Property,
)
from ..constants import *
from ..struct import BELGraph
from ..utils import hash_edge, hash_node, parse_datetime

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

    def query_nodes(self, node_id=None, bel=None, type=None, namespace=None, name=None, modification_type=None,
                    modification_name=None, as_dict_list=False):
        """Builds and runs a query over all nodes in the PyBEL cache.

        :param int node_id: The node ID to get
        :param str bel: BEL term that describes the biological entity. e.g. ``p(HGNC:APP)``
        :param str type: Type of the biological entity. e.g. Protein
        :param str namespace: Namespace keyword that is used in BEL. e.g. HGNC
        :param str name: Name of the biological entity. e.g. APP
        :param str modification_name:
        :param str modification_type:
        :param bool as_dict_list: Identifies whether the result should be a list of dictionaries or a list of
                            :class:`Node` objects.
        :return: A list of the fitting nodes as :class:`Node` objects or dicts.
        :rtype: list[Node]
        """
        q = self.session.query(Node)

        if node_id and isinstance(node_id, int):
            q = q.filter_by(id=node_id)

        else:
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

            if modification_type or modification_name:
                q = q.join(Modification)
                if modification_type:
                    q = q.filter(Modification.modType.like(modification_type))
                if modification_name:
                    q = q.filter(Modification.modName.like(modification_name))

        result = q.all()

        if not as_dict_list:
            return result

        dict_list = []

        for node in result:
            node_dict = node.to_json()
            node_dict['bel'] = node.bel
            dict_list.append({
                'data': node.to_json(),
                'bel': node.bel
            })

        return dict_list

    def count_edges(self):
        """Counts the number of edges in the cache

        :rtype: int
        """
        return self.session.query(func.count(Edge.id)).scalar()

    def get_edge_by_tuple(self, u, v, d):
        """Looks up an edge by PyBEL edge tuple

        :param tuple u: A PyBEL node tuple
        :param tuple v: A PyBEL node tuple
        :param dict d:
        :rtype: Edge
        """
        return self.get_edge_by_hash(hash_edge(u, v, None, d))

    def query_edges(self, edge_id=None, bel=None, source=None, target=None, relation=None, citation=None,
                    evidence=None, annotation=None, property=None, as_dict_list=False):
        """Builds and runs a query over all edges in the PyBEL cache.

        :param int edge_id: The edge identifier
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
        :param bool as_dict_list: Identifies whether the result should be a list of dictionaries or a list of
                                    :class:`Edge` objects.
        :rtype: list[Edge]
        """
        q = self.session.query(Edge)

        if edge_id and isinstance(edge_id, int):
            q = q.filter_by(id=edge_id)

        else:
            if bel:
                q = q.filter(Edge.bel.like(bel))

            if relation:
                q = q.filter(Edge.relation.like(relation))

            if annotation:
                q = q.join(AnnotationEntry, Edge.annotations)
                if isinstance(annotation, dict):
                    q = q.join(Annotation).filter(Annotation.keyword.in_(list(annotation.keys())))
                    q = q.filter(AnnotationEntry.name.in_(list(annotation.values())))

                elif isinstance(annotation, str):
                    q = q.filter(AnnotationEntry.name.like(annotation))

            if source:
                if isinstance(source, str):
                    source = self.query_nodes(bel=source)
                    if len(source) == 0:
                        return []
                    source = source[0]

                if isinstance(source, Node):
                    q = q.filter(Edge.source == source)

                    # ToDo: in_() not yet supported for relations
                    # elif isinstance(source, list) and len(source) > 0:
                    #    if isinstance(source[0], Node):
                    #        q = q.filter(Edge.source.in_(source))

            if target:
                if isinstance(target, str):
                    target = self.query_nodes(bel=target)[0]

                if isinstance(target, Node):
                    q = q.filter(Edge.target == target)

                    # elif isinstance(target, list) and len(target) > 0:
                    #    if isinstance(target[0], Node):
                    #        q = q.filter(Edge.source.in_(target))

            if citation or evidence:
                q = q.join(Evidence)

                if citation:
                    if isinstance(citation, Citation):
                        q = q.filter(Evidence.citation == citation)

                    elif isinstance(citation, list) and isinstance(citation[0], Citation):
                        q = q.filter(Evidence.citation.in_(citation))

                    elif isinstance(citation, str):
                        q = q.join(Citation).filter(Citation.reference.like(citation))

                if evidence:
                    if isinstance(evidence, Evidence):
                        q = q.filter(Edge.evidence == evidence)

                    elif isinstance(evidence, str):
                        q = q.filter(Evidence.text.like(evidence))

            if property:
                q = q.join(Property, Edge.properties)

                if isinstance(property, Property):
                    q = q.filter(Property.id == property.id)
                elif isinstance(property, int):
                    q = q.filter(Property.id == property)

        result = q.all()

        if not as_dict_list:
            return result

        return [
            edge.to_json()
            for edge in result
        ]

    def query_citations(self, citation_id=None, type=None, reference=None, name=None, author=None, date=None,
                        evidence_text=None, as_dict_list=False):
        """Builds and runs a query over all citations in the PyBEL cache.

        :param int citation_id:
        :param str type: Type of the citation. e.g. PubMed
        :param str reference: The identifier used for the citation. e.g. PubMed_ID
        :param str name: Title of the citation.
        :param str or list[str] author: The name or a list of names of authors participated in the citation.
        :param date: Publishing date of the citation.
        :type date: str or datetime.date
        :param str evidence_text:
        :param bool as_dict_list: Identifies whether the result should be a list of dictionaries or a list of
                            :class:`Citation` objects.
        :return: List of :class:`Citation` objects or corresponding dicts.
        :rtype: list[Citation] or dict
        """
        q = self.session.query(Citation)

        if citation_id and isinstance(citation_id, int):
            q = q.filter_by(id=citation_id)

        else:
            if author is not None:
                q = q.join(Author, Citation.authors)
                if isinstance(author, str):
                    q = q.filter(Author.name.like(author))
                elif isinstance(author, list):
                    q = q.filter(Author.name.in_(author))

            if type:
                q = q.filter(Citation.type.like(type))

            if reference:
                q = q.filter(Citation.reference == reference)

            if name:
                q = q.filter(Citation.name.like(name))

            if date:
                if isinstance(date, datetime.date):
                    q = q.filter(Citation.date == date)
                elif isinstance(date, str):
                    q = q.filter(Citation.date == parse_datetime(date))

            if evidence_text:
                q = q.join(Evidence).filter(Evidence.text.like(evidence_text))

        citations = q.all()

        if not as_dict_list:
            return citations

        return [
            citation.to_json()
            for citation in citations
        ]

    def query_node_properties(self, property_id=None, participant=None, modifier=None, as_dict_list=False):
        """Builds and runs a query over all property entries in the database.

        :param int property_id: Database primary identifier.
        :param str participant: The participant that is effected by the property (OBJECT or SUBJECT)
        :param str modifier: The modifier of the property.
        :param bool as_dict_list: Identifies weather the result should be a list of dictionaries or a list of
                             :class:`Property` objects.
        :rtype: list[Property]
        """
        q = self.session.query(Property)

        if property_id:
            q = q.filter_by(id=property_id)

        else:
            if participant:
                q = q.filter(Property.participant.like(participant))

            if modifier:
                q = q.filter(Property.modifier.like(modifier))

        result = q.all()

        if not as_dict_list:
            return result

        return [
            prop.data
            for prop in result
        ]

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
            raise ValueError

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
