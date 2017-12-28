# -*- coding: utf-8 -*-

from uuid import uuid4

from pybel.manager.models import Annotation, AnnotationEntry, Namespace, NamespaceEntry
from pybel.utils import subdict_matches


def any_subdict_matches(dict_of_dicts, query_dict):
    """Checks if dictionary target_dict matches one of the subdictionaries of a

    :param dict[any,dict] dict_of_dicts: dictionary of dictionaries
    :param dict query_dict: dictionary
    :return: if dictionary target_dict matches one of the subdictionaries of a
    :rtype: bool
    """
    return any(
        subdict_matches(sub_dict, query_dict)
        for sub_dict in dict_of_dicts.values()
    )


def make_dummy_namespaces(manager, graph, namespaces):
    """
    :param pybel.manager.Manager manager:
    :param pybel.BELGraph graph:
    :param dict namespaces:
    """
    for keyword, names in namespaces.items():
        url = str(uuid4())
        graph.namespace_url[keyword] = url

        namespace = Namespace(keyword=keyword, url=url)
        manager.session.add(namespace)
        manager.namespace_model[url] = namespace

        for name in names:
            entry = NamespaceEntry(name=name, namespace=namespace)
            manager.session.add(entry)
            manager.namespace_object_cache[url][entry.name] = entry

        manager.session.commit()


def make_dummy_annotations(manager, graph, annotations):
    """
    :param pybel.manager.Manager manager:
    :param pybel.BELGraph graph:
    :param dict annotations:
    """
    for keyword, names in annotations.items():
        url = str(uuid4())
        graph.annotation_url[keyword] = url

        annotation = Annotation(keyword=keyword, url=url)
        manager.session.add(annotation)
        manager.annotation_model[url] = annotation

        for name in names:
            entry = AnnotationEntry(name=name, annotation=annotation)
            manager.session.add(entry)
            manager.annotation_object_cache[url][entry.name] = entry

        manager.session.commit()


def any_dict_matches(dict_of_dicts, query_dict):
    """

    :param dict_of_dicts:
    :param query_dict:
    :return:
    """
    return any(
        query_dict == sd
        for sd in dict_of_dicts.values()
    )
