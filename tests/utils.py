# -*- coding: utf-8 -*-

from uuid import uuid4

from pybel.manager.models import Annotation, AnnotationEntry, Namespace, NamespaceEntry


def make_dummy_namespaces(manager, graph, namespaces):
    """
    :param pybel.manager.Manager manager:
    :param pybel.BELGraph graph:
    :param dict[str,iter[str]] namespaces:
    """
    for keyword, names in namespaces.items():
        url = str(uuid4())
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
        url = str(uuid4())
        graph.annotation_url[keyword] = url

        annotation = Annotation(keyword=keyword, url=url)
        manager.session.add(annotation)
        manager.annotation_model[url] = annotation

        for name in names:
            entry = manager.annotation_object_cache[url][entry.name] = AnnotationEntry(name=name, annotation=annotation)
            manager.session.add(entry)

        manager.session.commit()
