# -*- coding: utf-8 -*-

"""A manager for looking up nodes."""

from typing import List, Optional

from .base_manager import BaseManager
from .models import Author, Citation, Edge, Evidence, Node
from ..constants import CITATION_TYPE_PUBMED
from ..dsl import BaseEntity
from ..utils import hash_citation


class LookupManager(BaseManager):
    """Groups functions for looking up entries by hashes."""

    def get_dsl_by_hash(self, node_hash: str) -> Optional[BaseEntity]:
        """Look up a node by the hash and returns the corresponding PyBEL node tuple."""
        node = self.get_node_by_hash(node_hash)
        if node is not None:
            return node.as_bel()

    def get_node_by_hash(self, node_hash: str) -> Optional[Node]:
        """Look up a node by its hash."""
        return self.session.query(Node).filter(Node.sha512 == node_hash).one_or_none()

    def get_nodes_by_hashes(self, node_hashes: List[str]) -> List[Node]:
        """Look up several nodes by their hashes."""
        return self.session.query(Node).filter(Node.sha512.in_(node_hashes)).all()

    def get_node_by_dsl(self, node_dict: BaseEntity) -> Optional[Node]:
        """Look up a node by its data dictionary by hashing it then using :func:`get_node_by_hash`."""
        return self.get_node_by_hash(node_dict.as_sha512())

    def get_edge_by_hash(self, edge_hash: str) -> Optional[Edge]:
        """Look up an edge by the hash of a PyBEL edge data dictionary."""
        return self.session.query(Edge).filter(Edge.sha512 == edge_hash).one_or_none()

    def get_edges_by_hashes(self, edge_hashes: List[str]) -> List[Edge]:
        """Look up several edges by hashes of their PyBEL edge data dictionaries."""
        return self.session.query(Edge).filter(Edge.sha512.in_(edge_hashes)).all()

    def get_citation_by_pmid(self, pubmed_identifier: str) -> Optional[Citation]:
        """Get a citation object by its PubMed identifier."""
        return self.get_citation_by_reference(reference=pubmed_identifier, type=CITATION_TYPE_PUBMED)

    def get_citation_by_reference(self, type: str, reference: str) -> Optional[Citation]:
        """Get a citation object by its type and reference."""
        citation_hash = hash_citation(type=type, reference=reference)
        return self.get_citation_by_hash(citation_hash)

    def get_citation_by_hash(self, citation_hash: str) -> Optional[Citation]:
        """Get a citation object by its hash."""
        return self.session.query(Citation).filter(Citation.sha512 == citation_hash).one_or_none()

    def get_author_by_name(self, name: str) -> Optional[Author]:
        """Get an author by name, if it exists in the database."""
        return self.session.query(Author).filter(Author.has_name(name)).one_or_none()

    def get_evidence_by_hash(self, evidence_hash: str) -> Optional[Evidence]:
        """Look up an evidence by its hash."""
        return self.session.query(Evidence).filter(Evidence.sha512 == evidence_hash).one_or_none()
