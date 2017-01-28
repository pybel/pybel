"""

The pybel.manager module serves as an interface between the BEL graph data structure and underlying relational
databases. Its inclusion allows for the caching of namespaces and annotations for much faster lookup than
downloading and parsing upon each compilation.

"""

from .cache import CacheManager
from .graph_cache import GraphCacheManager, to_database, from_database

__all__ = ['CacheManager', 'GraphCacheManager', 'to_database', 'from_database']
