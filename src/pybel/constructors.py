from .manager.cache import CacheManager
from .parser import MetadataParser


def build_metadata_parser(manager):
    if isinstance(manager, MetadataParser):
        return manager
    elif isinstance(manager, CacheManager):
        return MetadataParser(manager)
    elif isinstance(manager, str):
        return MetadataParser(CacheManager(connection=manager))
    else:
        return MetadataParser(CacheManager())
