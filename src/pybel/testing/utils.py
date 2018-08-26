# -*- coding: utf-8 -*-

"""Utilities for PyBEL testing."""

from uuid import uuid4

from requests.compat import urlparse

from ..constants import FRAUNHOFER_RESOURCES
from ..manager.models import Namespace, NamespaceEntry
from ..struct.summary import get_annotation_values_by_annotation
from ..struct.summary.node_summary import get_names


def get_uri_name(url):
    """Gets the file name from the end of the URL.

    Only useful for PyBEL's testing though since it looks specifically if the file is from the weird owncloud
    resources distributed by Fraunhofer.

    :type url: str
    :rtype: str
    """
    url_parsed = urlparse(url)

    if url.startswith(FRAUNHOFER_RESOURCES):
        return url_parsed.query.split('=')[-1]
    else:
        url_parts = url_parsed.path.split('/')
        return url_parts[-1]


def n():
    """Returns a UUID string for testing

    :rtype: str
    """
    return str(uuid4())[:15]


def make_dummy_namespaces(manager, graph, namespace_dict=None):
    """Make dummy namespaces for the test.

    :param pybel.manager.Manager manager:
    :type namespaces: dict[str,iter[str]]
    :param pybel.BELGraph graph:
    """
    node_names = get_names(graph)

    if namespace_dict:
        node_names.update(namespace_dict)

    for keyword, names in node_names.items():
        if keyword in graph.namespace_url and graph.namespace_url[keyword] in graph.uncached_namespaces:
            continue

        url = n()
        graph.namespace_url[keyword] = url

        namespace = Namespace(keyword=keyword, url=url)
        manager.session.add(namespace)

        for name in names:
            entry = NamespaceEntry(name=name, namespace=namespace)
            manager.session.add(entry)

        manager.session.commit()


def make_dummy_annotations(manager, graph):
    """Make dummy annotations for the test.

    :param pybel.manager.Manager manager:
    :param pybel.BELGraph graph:
    """
    annotation_names = get_annotation_values_by_annotation(graph)

    for keyword, names in annotation_names.items():
        url = n()
        graph.annotation_url[keyword] = url

        namespace = Namespace(keyword=keyword, url=url)
        manager.session.add(namespace)

        for name in names:
            entry = NamespaceEntry(name=name, namespace=namespace)
            manager.session.add(entry)

        manager.session.commit()
