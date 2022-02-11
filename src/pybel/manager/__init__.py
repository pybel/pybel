# -*- coding: utf-8 -*-

"""Managers and subclasses for PyBEL.

The :mod:`pybel.manager` module serves as an interface between the BEL graph data structure and underlying relational
databases. Its inclusion allows for the caching of namespaces and annotations for much faster lookup than
downloading and parsing upon each compilation.
"""

from . import (
    base_manager,
    cache_manager,
    citation_utils,
    database_io,
    make_json_serializable,
    models,
    query_manager,
)
from .base_manager import BaseManager, build_engine_session
from .cache_manager import Manager, NetworkManager
from .citation_utils import enrich_pmc_citations, enrich_pubmed_citations
from .database_io import from_database, to_database
from .models import (
    Author,
    Base,
    Citation,
    Edge,
    Evidence,
    Namespace,
    NamespaceEntry,
    Network,
    Node,
    edge_annotation,
    network_edge,
    network_node,
)
from .query_manager import QueryManager, graph_from_edges

__all__ = [
    "BaseManager",
    "build_engine_session",
    "Manager",
    "NetworkManager",
    "QueryManager",
    "graph_from_edges",
    "enrich_pubmed_citations",
    "enrich_pmc_citations",
    # I/O
    "from_database",
    "to_database",
    # Models
    "Base",
    "Namespace",
    "NamespaceEntry",
    "Network",
    "Node",
    "Author",
    "Citation",
    "Evidence",
    "Edge",
    "edge_annotation",
    "network_edge",
    "network_node",
]
