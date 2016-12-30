from .cache import BaseCacheManager, NoResultFound
from ..utils import download_url


class MapperManager(BaseCacheManager):
    def insert_equivalences(self, url, namespace_url):
        """Given a url to a .beleq file and its accompanying namespace url, populate the database"""
        config = download_url(url)

    def ensure_equivalences(self, url, namespace_url):
        """Check if the equivalence file is already loaded, and if not, load it"""

    def get_equivalence_by_entry(self, namespace_url, entry):
        """Gets the equivalence class """

    def get_equivalent_members(self, namespace_url, entry):
        """Given an entity, get a dictionary of equivalent entities {url: name"""
