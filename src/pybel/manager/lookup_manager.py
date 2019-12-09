# -*- coding: utf-8 -*-

"""A manager for looking up nodes."""

from typing import List, Optional

from sqlalchemy import and_

from .base_manager import BaseManager
from .models import Author, Citation, Edge, Evidence, Node
from ..constants import CITATION_TYPE_PUBMED
from ..dsl import BaseEntity


class LookupManager(BaseManager):
    """Groups functions for looking up entries by hashes."""

    def get_dsl_by_hash(self, node_hash: str) -> Optional[BaseEntity]:
        """Look up a node by the hash and returns the corresponding PyBEL node tuple."""
        node = self.get_node_by_hash(node_hash)
        if node is not None:
            return node.as_bel()

    def get_node_by_hash(self, node_hash: str) -> Optional[Node]:
        """Look up a node by its hash."""
        return self.session.query(Node).filter(Node.md5 == node_hash).one_or_none()

    def get_nodes_by_hashes(self, node_hashes: List[str]) -> List[Node]:
        """Look up several nodes by their hashes."""
        return self.session.query(Node).filter(Node.md5.in_(node_hashes)).all()

    def get_node_by_dsl(self, node: BaseEntity) -> Optional[Node]:
        """Look up a node by its data dictionary by hashing it then using :func:`get_node_by_hash`."""
        return self.get_node_by_hash(node.md5)

    def get_edge_by_hash(self, edge_hash: str) -> Optional[Edge]:
        """Look up an edge by the hash of a PyBEL edge data dictionary."""
        return self.session.query(Edge).filter(Edge.md5 == edge_hash).one_or_none()

    def get_edges_by_hashes(self, edge_hashes: List[str]) -> List[Edge]:
        """Look up several edges by hashes of their PyBEL edge data dictionaries."""
        return self.session.query(Edge).filter(Edge.md5.in_(edge_hashes)).all()

    def get_citation_by_pmid(self, pubmed_identifier: str) -> Optional[Citation]:
        """Get a citation object by its PubMed identifier."""
        return self.get_citation_by_reference(db_id=pubmed_identifier, db=CITATION_TYPE_PUBMED)

    def get_citation_by_reference(self, db: str, db_id: str) -> Optional[Citation]:
        """Get a citation object by its database and reference."""
        return self.session.query(Citation).filter(Citation.db == db, Citation.db_id == db_id).one_or_none()

    def get_citation_by_curie(self, curie: str) -> Optional[Citation]:
        """Get a citation object by its hash."""
        db, db_id = curie.split(':')
        return self.get_citation_by_reference(db=db, db_id=db_id)

    def get_author_by_name(self, name: str) -> Optional[Author]:
        """Get an author by name, if it exists in the database."""
        return self.session.query(Author).filter(Author.name == name).one_or_none()

    def get_evidence_by_hash(self, evidence_hash: str) -> Optional[Evidence]:
        """Look up an evidence by its hash."""
        return self.session.query(Evidence).filter(Evidence.md5 == evidence_hash).one_or_none()

    def get_evidence_by_reference_text(self, db: str, db_id: str, text: str) -> Optional[Evidence]:
        """Look up an evidence by its citation's database/identifier and text."""
        citation = self.get_citation_by_reference(db=db, db_id=db_id)
        if citation is not None:
            return self.get_evidence_by_citation_text(citation, text)

    def get_evidence_by_citation_text(self, citation: Citation, text: str) -> Optional[Evidence]:
        """Look up an evidence by its citation and text."""
        f = and_(Evidence.citation == citation, Evidence.text == text)
        return self.session.query(Evidence).filter(f).one_or_none()
