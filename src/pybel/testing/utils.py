# -*- coding: utf-8 -*-

"""Utilities for PyBEL testing."""

from uuid import uuid4

from requests.compat import urlparse

from ..manager import Manager
from ..manager.models import Namespace, NamespaceEntry
from ..struct import BELGraph
from ..struct.summary import (
    get_annotation_values_by_annotation,
    iter_annotation_value_pairs,
)
from ..struct.summary.node_summary import get_names

_FRAUNHOFER_RESOURCES = "https://owncloud.scai.fraunhofer.de/index.php/s/JsfpQvkdx3Y5EMx/download?path="


def get_uri_name(url: str) -> str:
    """Get the file name from the end of the URL."""
    url_parsed = urlparse(url)
    if url.startswith(_FRAUNHOFER_RESOURCES):
        return url_parsed.query.split("=")[-1]
    else:
        url_parts = url_parsed.path.split("/")
        return url_parts[-1]


def n() -> str:
    """Return a UUID string for testing."""
    return str(uuid4())[:15]


def make_dummy_namespaces(manager: Manager, graph: BELGraph) -> None:
    """Make dummy namespaces for the test."""
    for keyword, names in get_names(graph).items():
        graph.namespace_url[keyword] = url = n()

        namespace = Namespace(keyword=keyword, url=url)
        manager.session.add(namespace)

        for name in names:
            entry = NamespaceEntry(name=name, namespace=namespace)
            manager.session.add(entry)

    manager.session.commit()


def make_dummy_annotations(manager: Manager, graph: BELGraph):
    """Make dummy annotations for the test."""
    namespaces = {}
    for keyword, entity in iter_annotation_value_pairs(graph):
        namespace = namespaces.get(keyword)
        if namespace is None:
            graph.annotation_url[keyword] = url = n()
            namespace = Namespace(keyword=keyword, url=url, is_annotation=True)
            manager.session.add(namespace)

        entry = NamespaceEntry(name=entity.name, identifier=entity.identifier, namespace=namespace)
        manager.session.add(entry)

    manager.session.commit()
