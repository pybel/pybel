# -*- coding: utf-8 -*-

from .base_manager import BaseManager
from .models import Author, Citation, Edge, Evidence, Node
from ..constants import CITATION_TYPE_PUBMED
from ..tokens import hash_node_dict
from ..utils import hash_citation


class LookupManager(BaseManager):
    """Groups functions for looking up entries by hashes"""

    def get_node_by_hash(self, node_hash):
        """Looks up a node by the hash of a PyBEL node tuple

        :param str node_hash: The hash of a PyBEL node tuple from :func:`pybel.utils.hash_node`
        :rtype: Optional[Node]
        """
        return self.session.query(Node).filter(Node.sha512 == node_hash).one_or_none()

    def get_nodes_by_hashes(self, node_hashes):
        """Look up several nodes by hashes of their PyBEL node tuples.

        :param List[str] node_hashes: The hashes of PyBEL node tuples from :func:`pybel.utils.hash_node`
        :rtype: List[Node]
        """
        return self.session.query(Node).filter(Node.sha512.in_(node_hashes)).all()

    def get_node_by_dict(self, node_dict):
        """Looks up a node by its data dictionary by hashing it then using :func:`get_node_by_hash`

        :param dict node_dict: A PyBEL node data dictionary
        :rtype: Optional[Node]
        """
        return self.get_node_by_hash(hash_node_dict(node_dict))

    def get_edge_by_hash(self, edge_hash):
        """Looks up an edge by the hash of a PyBEL edge data dictionary

        :param str edge_hash: The hash of a PyBEL edge data dictionary from :func:`pybel.utils.hash_edge`
        :rtype: Optional[Edge]
        """
        return self.session.query(Edge).filter(Edge.sha512 == edge_hash).one_or_none()

    def get_edges_by_hashes(self, edge_hashes):
        """Looks up several edges by hashes of their PyBEL edge data dictionaries.

        :param List[str] edge_hashes: The hashes of PyBEL edge data dictionaries from :func:`pybel.utils.hash_edge`
        :rtype: List[Edge]
        """
        return self.session.query(Edge).filter(Edge.sha512.in_(edge_hashes)).all()

    def get_citation_by_reference(self, type, reference):
        """Gets a citation object by its type and reference

        :param str type: The reference type
        :param str reference: The identifier in the source (e.g., PubMed identifier)
        :rtype: Optional[Citation]
        """
        citation_hash = hash_citation(type=type, reference=reference)
        return self.get_citation_by_hash(citation_hash)

    def get_citation_by_pmid(self, pubmed_identifier):
        """Gets a citation object by its PubMed identifier

        :param str pubmed_identifier: The PubMed identifier
        :rtype: Optional[Citation]
        """
        return self.get_citation_by_reference(reference=pubmed_identifier, type=CITATION_TYPE_PUBMED)

    def get_citation_by_hash(self, citation_hash):
        """Gets a citation object by its hash

        :param str citation_hash: The hash of the citation
        :rtype: Optional[Citation]
        """
        return self.session.query(Citation).filter(Citation.sha512 == citation_hash).one_or_none()

    def get_author_by_name(self, name):
        """Gets an author by name if they exist in the database

        :param str name: An author's name
        :rtype: Optional[Author]
        """
        return self.session.query(Author).filter(Author.name == name).one_or_none()

    def get_evidence_by_hash(self, evidence_hash):
        """Looks up evidence by its hash

        :param str evidence_hash:
        :rtype: Optional[Evidence]
        """
        return self.session.query(Evidence).filter(Evidence.sha512 == evidence_hash).one_or_none()
