# -*- coding: utf-8 -*-

"""This module interfaces with Artifactory to find the appropriate BEL resources"""

import logging

from artifactory import ArtifactoryPath

from .utils import get_iso_8601_date

log = logging.getLogger(__name__)

ARTY_BASE = 'https://arty.scai.fraunhofer.de/artifactory/bel/'
ARTY_NS = ARTY_BASE + 'namespace/'
ARTY_ANNO = ARTY_BASE + 'annotation/'
ARTY_BEL = ARTY_BASE + 'knowledge/'


def get_arty_namespace_module(namespace):
    """

    :param namespace:
    :return:
    """
    return '{}{}/'.format(ARTY_NS, namespace)


def get_arty_namespace(namespace, version):
    """

    :param namespace:
    :param version:
    :return:
    """
    return '{}-{}.belns'.format(namespace, version)


def get_arty_namespace_url(namespace, version):
    """Gets a BEL namespace file from artifactory given the name and version"""
    return '{}{}'.format(get_arty_namespace_module(namespace), get_arty_namespace(namespace, version))


def get_arty_annotation_module(module_name):
    """

    :param module_name:
    :return:
    """
    return '{}{}/'.format(ARTY_ANNO, module_name)


def get_arty_annotation(module_name, version):
    """

    :param module_name:
    :param version:
    :return:
    """
    return '{}-{}.belanno'.format(module_name, version)


def get_arty_annotation_url(module_name, version):
    """Gets a BEL annotation file from artifactory given the name and version


    """
    return '{}{}'.format(get_arty_annotation_module(module_name), get_arty_annotation(module_name, version))


def get_arty_knowledge_module(module_name):
    """

    :param module_name:
    :return:
    """
    return '{}{}/'.format(ARTY_BEL, module_name)


def get_arty_knowledge(module_name, version):
    """Formats the module name and version for a BEL Script

    :param str module_name:
    :param str version:
    """
    return '{}-{}.bel'.format(module_name, version)


def get_arty_knowledge_url(module_name, version):
    """Gets a BEL knowledge file from artifactory given the name and version

    :param str module_name:
    :param str version:
    :rtype: str
    """
    return '{}{}'.format(get_arty_knowledge_module(module_name), get_arty_knowledge(module_name, version))


def get_today_arty_namespace(module_name):
    """Gets the right name for the next version of the namespace

    :param str module_name:
    :rtype: str
    """
    return get_arty_namespace(module_name, get_iso_8601_date())


def get_today_arty_annotation(module_name):
    """Gets the right name for the next version of the annotation

    :param str module_name:
    :rtype: str
    """
    return get_arty_annotation(module_name, get_iso_8601_date())


def get_today_arty_knowledge(module_name):
    """

    :param str module_name:
    :rtype: str
    """
    return get_arty_knowledge(module_name, get_iso_8601_date())


def _get_path_helper(module_name, getter):
    """Helps get the Artifactory path for a certain module

    :param str module_name: The name of the module
    :param types.FunctionType getter: The function that gets the modules from the Artifactory repository
    :rtype: artifactory.ArtifactoryPath
    """
    return ArtifactoryPath(getter(module_name))


def get_namespace_history(module_name):
    """Gets the Artifactory path for a namespace module

    :param str module_name: The name of the namespace module
    :rtype: artifactory.ArtifactoryPath
    """
    return _get_path_helper(module_name, get_arty_namespace_module)


def get_annotation_history(module_name):
    """Gets the Artifactory path for an annotation module

    :param str module_name: The name of the annotation module
    :rtype: artifactory.ArtifactoryPath
    """
    return _get_path_helper(module_name, get_arty_annotation_module)


def get_knowledge_history(module_name):
    """Gets the Artifactory path for a knowledge module

    :param str module_name: The name of the knowledge module
    :rtype: artifactory.ArtifactoryPath
    """
    return _get_path_helper(module_name, get_arty_knowledge_module)


def _get_latest_arty_helper(module_name, getter):
    """Helps get the latest path for a given BEL module by paremetrizing the getter"""
    path = _get_path_helper(module_name, getter)
    mp = max(path)
    return mp.as_posix()


def get_latest_arty_namespace(module_name):
    """Gets the latest path for this BEL namespace module. For historical reasons, some of these are not the same
    as the keyword. For example, the module name for HGNC is ``hgnc-human-genes`` due to the Selventa nomenclature.
    See https://arty.scai.fraunhofer.de/artifactory/bel/namespace/ for the entire manifest of available namespaces.

    :param str module_name: The BEL namespace module name
    :return: The URL of the latest version of this namespace
    :rtype: str
    """
    return _get_latest_arty_helper(module_name, get_arty_namespace_module)


def get_latest_arty_annotation(module_name):
    """Gets the latest path for this BEL annotation module

    :param str module_name: The BEL annotation module name
    :return: The URL of the latest version of this annotation
    :rtype: str
    """
    return _get_latest_arty_helper(module_name, get_arty_annotation_module)


def get_latest_arty_knowledge(module_name):
    """Gets the latest path for this BEL annotation module

    :param str module_name: The BEL knowledge module name
    :return: The URL of the latest version of this knowledge document
    :rtype: str
    """
    return _get_latest_arty_helper(module_name, get_arty_knowledge_module)
