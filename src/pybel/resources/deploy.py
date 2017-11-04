# -*- coding: utf-8 -*-

import logging
import os

from artifactory import ArtifactoryPath

from .arty import (
    get_arty_annotation_module, get_arty_knowledge_module, get_arty_namespace_module,
    get_today_arty_annotation, get_today_arty_knowledge, get_today_arty_namespace,
)
from .definitions import get_bel_resource_hash

log = logging.getLogger(__name__)


def get_arty_auth():
    """Gets the arty authentication tuple from the environment variables ``ARTY_USERNAME`` and ``ARTY_PASSWORD``,
    respectively.

    :rtype: tuple[str]
    """
    return os.environ['ARTY_USERNAME'], os.environ['ARTY_PASSWORD']


def _deploy_helper(filename, module_name, get_module, get_today_fn, hash_check=True, auth=None):
    """Deploys a file to the Artifactory BEL namespace cache

    :param str filename: The physical path
    :param str module_name: The name of the module to deploy to
    :param tuple[str] auth: A pair of (str username, str password) to give to the auth keyword of the constructor of
                            :class:`artifactory.ArtifactoryPath`. Defaults to the result of :func:`get_arty_auth`.
    :return: The resource path, if it was deployed successfully, else none.
    :rtype: str
    """
    path = ArtifactoryPath(
        get_module(module_name),
        auth=get_arty_auth() if auth is None else auth
    )
    path.mkdir(exist_ok=True)

    if hash_check:
        deployed_semantic_hashes = {
            get_bel_resource_hash(subpath.as_posix())
            for subpath in path
        }

        semantic_hash = get_bel_resource_hash(filename)

        if semantic_hash in deployed_semantic_hashes:
            return  # Don't deploy if it's already uploaded

    target = path / get_today_fn(module_name)
    target.deploy_file(filename)

    log.info('deployed %s', module_name)

    return target.as_posix()


def deploy_namespace(filename, module_name, hash_check=True, auth=None):
    """Deploys a file to the Artifactory BEL namespace cache

    :param str filename: The physical path
    :param str module_name: The name of the module to deploy to
    :param bool hash_check: Ensure the hash is unique before deploying
    :param tuple[str] auth: A pair of (str username, str password) to give to the auth keyword of the constructor of
                            :class:`artifactory.ArtifactoryPath`. Defaults to the result of :func:`get_arty_auth`.
    :return: The resource path, if it was deployed successfully, else none.
    :rtype: str
    """
    return _deploy_helper(
        filename,
        module_name,
        get_arty_namespace_module,
        get_today_arty_namespace,
        hash_check=hash_check,
        auth=auth
    )


def deploy_knowledge(filename, module_name, auth=None):
    """Deploys a file to the Artifactory BEL knowledge cache

    :param str filename: The physical file path
    :param str module_name: The name of the module to deploy to
    :param tuple[str] auth: A pair of (str username, str password) to give to the auth keyword of the constructor of
                            :class:`artifactory.ArtifactoryPath`. Defaults to the result of :func:`get_arty_auth`.
    :return: The resource path, if it was deployed successfully, else none.
    :rtype: str
    """
    return _deploy_helper(
        filename,
        module_name,
        get_arty_knowledge_module,
        get_today_arty_knowledge,
        hash_check=False,
        auth=auth
    )


def deploy_annotation(filename, module_name, hash_check=True, auth=None):
    """Deploys a file to the Artifactory BEL annotation cache

    :param str filename: The physical file path
    :param str module_name: The name of the module to deploy to
    :param bool hash_check: Ensure the hash is unique before deploying
    :param tuple[str] auth: A pair of (str username, str password) to give to the auth keyword of the constructor of
                            :class:`artifactory.ArtifactoryPath`. Defaults to the result of :func:`get_arty_auth`.
    :return: The resource path, if it was deployed successfully, else none.
    :rtype: str
    """
    return _deploy_helper(
        filename,
        module_name,
        get_arty_annotation_module,
        get_today_arty_annotation,
        hash_check=hash_check,
        auth=auth
    )


def deploy_directory(directory, auth=None):
    """Uploads all stuff from a directory to artifactory

    :param str directory: the path to a directory
    :param tuple[str] auth: A pair of (str username, str password) to give to the auth keyword of the constructor of
                            :class:`artifactory.ArtifactoryPath`. Defaults to the result of :func:`get_arty_auth`.
    """
    for file in os.listdir(directory):
        full_path = os.path.join(directory, file)

        if file.endswith('.belanno'):
            name = file[:-8]
            log.info('Uploading annotation %s', full_path)
            deploy_annotation(full_path, name, auth=auth)
        elif file.endswith('.belns'):
            name = file[:-6]
            log.info('Uploading namespace %s', full_path)
            deploy_namespace(full_path, name, auth=auth)
        elif file.endswith('.bel'):
            name = file[:-4]
            log.info('Uploading knowledge %s', full_path)
            deploy_knowledge(full_path, name, auth=auth)
