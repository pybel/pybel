import logging
import os
import time
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, exists
from sqlalchemy.orm import sessionmaker, scoped_session

from . import database_models
from .database_models import NAMESPACE_TABLE_NAME, NAMESPACENAME_TABLE_NAME
from .defaults import default_namespaces
from .. import utils

log = logging.getLogger('pybel')

pybel_data = os.path.expanduser('~/.pybel/data')
if not os.path.exists(pybel_data):
    os.makedirs(pybel_data)


class NamespaceCache:
    def __init__(self, conn=None, setup_default_cache=False, log_sql=False):
        """
        :param: conn: Database connection string. Defaults to 'sqlite:///namespaceCache.db'
        :type: str
        :param: setup_cache: Weather or not the namespace cache should be setted up on initiation.
        :type: bool
        :param: sql_echo: Weather or not echo the running sql code.
        :type: bool
        """
        conn = conn if conn is not None else 'sqlite:///' + os.path.join(pybel_data, 'namespace_cache.db')
        log.info('Loading namespace cache from {}'.format(conn))
        start_time = time.time()
        self.eng = create_engine(conn, echo=log_sql)
        self.sesh = scoped_session(sessionmaker(bind=self.eng, autoflush=False, expire_on_commit=False))
        self.cache = {}

        self.setup_database()
        if setup_default_cache:
            self.ensure_cache()

        log.info("Initiation of namespace cache took {runtime:3.2f}s".format(runtime=(time.time() - start_time)))

    def __insert_namespace(self, namespace_url):
        """Inserts namespace and names into namespace cache db.

        :param namespace_url: URL of the namespace definition file (.belns)
        """
        ns_config = utils.download_url(namespace_url)

        namespace_key = ns_config['Namespace']['Keyword']
        creationDateTime = datetime.strptime(ns_config['Namespace']['CreatedDateTime'], '%Y-%m-%dT%H:%M:%S')
        pubDate = datetime.strptime(ns_config['Citation']['PublishedDate'], '%Y-%m-%d') if 'PublishedDate' in ns_config[
            'Citation'] else None

        namespace_insert_values = [{
            'url': namespace_url,
            'author': ns_config['Author']['NameString'],
            'keyword': namespace_key,
            'createdDateTime': creationDateTime,
            'pubDate': pubDate,
            'copyright': ns_config['Author']['CopyrightString'],
            'version': ns_config['Namespace']['VersionString'],
            'contact': ns_config['Author']['ContactInfoString']
        }]

        self.cache[namespace_url] = dict(ns_config['Values'])

        namespace_check = self.check_namespace(namespace_key)

        if namespace_check:
            namespace_old = self.sesh.query(database_models.Namespace).filter_by(
                keyword=namespace_check['keyword'],
                version=namespace_check[
                    'version']).first()

            if not namespace_old.createdDateTime < creationDateTime:
                return namespace_key, namespace_old.createdDateTime, None

            else:
                self.__insert_namespace_helper(namespace_insert_values, self.cache[namespace_url])
                return namespace_key, creationDateTime, namespace_old

        self.__insert_namespace_helper(namespace_insert_values, self.cache[namespace_url])

        return namespace_key, creationDateTime, None

    def __insert_namespace_helper(self, ns_insert_values, names_dict):
        namespace_entry = self.eng.execute(database_models.Namespace.__table__.insert(), ns_insert_values)
        namespace_pk = namespace_entry.inserted_primary_key[0]

        name_insert_values = [{'namespace_id': namespace_pk, 'name': name, 'encoding': encoding} for
                              name, encoding in names_dict.items()]

        self.eng.execute(database_models.NamespaceName.__table__.insert(), name_insert_values)

    def __cached_namespaces(self):
        """
        Returns the cached namespaces as dictionary.
        """
        namespace_dataframe = pd.read_sql_table(NAMESPACE_TABLE_NAME, self.eng)
        name_dataframe = pd.read_sql_table(NAMESPACENAME_TABLE_NAME, self.eng)
        namespaces_names_dataframe = namespace_dataframe.merge(name_dataframe,
                                                               left_on='id',
                                                               right_on='namespace_id',
                                                               how='inner')
        grouped_dataframe = namespaces_names_dataframe[['url', 'name', 'encoding']].groupby("url")
        self.cache = {url: pd.Series(group.encoding.values, index=group.name).to_dict() for url, group in
                      grouped_dataframe}

    def setup_database(self, drop_existing=False):
        """Sets the database with the needed tables.

        :param drop_existing: Indicates if exising tables should be dropped and the cache should be reset.
        :type drop_existing: bool
        """
        start_time = time.time()
        if drop_existing:
            database_models.Base.metadata.drop_all(self.eng)
            log.info("Database was dropped! ({runtime:3.2f}sec.)".format(runtime=(time.time() - start_time)))
        database_models.Base.metadata.create_all(self.eng, checkfirst=True)

    def ensure_cache(self, namespace_urls=None):
        """Checks if a namespace cache already exists in given database and loads the namespace_cache dict.

        :param namespace_urls: Dictionary configuration see: defaults.py
        :type namespace_definiton: dict
        """
        start_time = time.time()
        namespace_urls = namespace_urls if namespace_urls else default_namespaces
        if self.eng.dialect.has_table(self.eng, NAMESPACE_TABLE_NAME):

            if self.sesh.query(database_models.Namespace).first():
                self.__cached_namespaces()
                log.info("Namespace cache already exists  {:.02}s".format(time.time() - start_time))
            else:
                for url in namespace_urls:
                    self.__insert_namespace(url)
                log.info("Database allready exists and namespace cache gets created ({runtime:3.2f}sec.)".format(
                    runtime=(time.time() - start_time)))

        else:
            self.setup_database()
            self.ensure_cache(namespace_urls)
            log.info("New database is setup and cache was created! ({runtime:3.2f})".format(
                runtime=(time.time() - start_time)))

    def update_namespace_cache(self, namespace_urls=None, overwrite_old_namespaces=True):
        """Updates the namespace cache DB with given namespace definition dictionary (see defaults.py)

        :param namespace_urls: List of namespace files by url
        :type namespace_urls: list
        :param overwrite_old_namespaces: Indicates if outdated namespaces should be overwritten
        :type overwrite_old_namespaces: bool
        """
        namespace_urls = namespace_urls if namespace_urls is not None else default_namespaces
        if self.eng.dialect.has_table(self.eng, NAMESPACE_TABLE_NAME):
            for url in namespace_urls:
                self.update_namespace(url, overwrite_old_namespaces)

        else:
            self.setup_database()
            self.update_namespace_cache(namespace_urls, overwrite_old_namespaces)

    def update_namespace(self, namespace_url, remove_old_namespace=True):
        """
        Checks if a namespace that is given by url is already in namespace cache and if so, if it is up to date.
        Works for urls like: http://resource.belframework.org/belframework/20150611/namespace/
        """
        start_time = time.time()

        if self.sesh.query(exists().where(database_models.Namespace.url == namespace_url)).scalar():
            return

        namespace_key, creationDateTime, namespace_old = self.__insert_namespace(namespace_url)

        if namespace_old and remove_old_namespace and namespace_old.createdDateTime < creationDateTime:
            log.warning(
                "Old namespace '{ns_key}' [{ns_old_url}] will be removed from cache database due to updated version [{ns_new_url}]".format(
                    ns_key=namespace_old.keyword,
                    ns_old_url=namespace_old.url,
                    ns_new_url=namespace_url))
            old_dateTime = namespace_old.createdDateTime
            self.remove_namespace(namespace_old.url, namespace_old.createdDateTime)

            log.info(
                "'{namespace_keyword}' was updated from v.{version_old} to v.{version_new} ({runtime:3.2f}sec.)".format(
                    namespace_keyword=namespace_key,
                    version_old=old_dateTime,
                    version_new=creationDateTime,
                    runtime=time.time() - start_time))

    def check_namespace(self, namespace_key):
        """Check if namespace exists and what version is in the cache.

        :param namesapce_key: Keyword for a namespace. i.e.: 'HGNC'
        :type namespace_key: str
        :return: None (doese not exist) or number of namesapces.
        :rtype: None or dict
        """
        namespace_old = self.sesh.query(database_models.Namespace).filter_by(keyword=namespace_key).first()
        if namespace_old:
            return {
                'keyword': namespace_old.keyword,
                'version': namespace_old.version,
                'url': namespace_old.url,
                'createdDateTime': namespace_old.createdDateTime,
                'pubDate': namespace_old.pubDate,
                'copyright': namespace_old.copyright,
                'author': namespace_old.author,
                'contact': namespace_old.contact
            }

    def remove_namespace(self, namespace_url, created_date_time):
        """Removes namespace from cache by url.

        :param namespace_url: URL to the namespace definition file (.belns)
        :type namespace_url: str
        :param created_date_time: Date and time of the keyword inside the document given by namespace_url.
        format like: 2015-06-11T19:51:19
        :type created_date_time: str

        """
        ns_to_remove = created_date_time if isinstance(created_date_time, datetime) else datetime.strptime(
            created_date_time, '%Y-%m-%dT%H:%M:%S')
        namespace = self.sesh.query(database_models.Namespace).filter_by(url=namespace_url,
                                                                         createdDateTime=ns_to_remove).first()
        if namespace:
            self.sesh.delete(namespace)
            self.sesh.commit()
            del self.cache[namespace_url]
