# -*- coding: utf-8 -*-

from .manager.cache import CacheManager
from .parser import MetadataParser


def build_metadata_parser(manager=None):
    """Builds a metadata parser
    
    :param manager: 
    :type manager: None or str or CacheManager or MetadataParser
    :return: A metadata parser
    :rtype: MetadataParser
    """
    if isinstance(manager, MetadataParser):
        return manager

    elif isinstance(manager, CacheManager):
        return MetadataParser(manager)

    elif isinstance(manager, str):
        return MetadataParser(CacheManager(connection=manager))

    return MetadataParser(CacheManager())
