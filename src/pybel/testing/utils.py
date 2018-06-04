# -*- coding: utf-8 -*-

"""Utilities for PyBEL testing."""

from uuid import uuid4

from requests.compat import urlparse

from ..constants import FRAUNHOFER_RESOURCES
from ..manager.models import Annotation, AnnotationEntry, Namespace, NamespaceEntry


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


def make_dummy_namespaces(manager, graph, namespaces):
    """
    :param pybel.manager.Manager manager:
    :param pybel.BELGraph graph:
    :param dict[str,iter[str]] namespaces:
    """
    for keyword, names in namespaces.items():
        url = n()
        graph.namespace_url[keyword] = url

        namespace = Namespace(keyword=keyword, url=url)
        manager.session.add(namespace)
        manager.namespace_model[url] = namespace

        for name in names:
            entry = manager.namespace_object_cache[url][entry.name] = NamespaceEntry(name=name, namespace=namespace)
            manager.session.add(entry)

        manager.session.commit()


def make_dummy_annotations(manager, graph, annotations):
    """
    :param pybel.manager.Manager manager:
    :param pybel.BELGraph graph:
    :param dict[str,iter[str]] annotations:
    """
    for keyword, names in annotations.items():
        url = n()
        graph.annotation_url[keyword] = url

        annotation = Annotation(keyword=keyword, url=url)
        manager.session.add(annotation)
        manager.annotation_model[url] = annotation

        for name in names:
            entry = manager.annotation_object_cache[url][entry.name] = AnnotationEntry(name=name, annotation=annotation)
            manager.session.add(entry)

        manager.session.commit()
