import logging
import os
import time
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, exists
from sqlalchemy.orm import sessionmaker, scoped_session

from . import database_models
from .database_models import DEFINITION_TABLE_NAME, CONTEXT_TABLE_NAME, DEFINITION_ANNOTATION, DEFINITION_NAMESPACE
from .defaults import default_namespaces, default_annotations
from .. import utils

log = logging.getLogger('pybel')

DEFAULT_DEFINITION_CACHE_NAME = 'namespace_cache.db'

pybel_data = os.path.expanduser('~/.pybel/data')
if not os.path.exists(pybel_data):
    os.makedirs(pybel_data)

DEFAULT_CACHE_LOCATION = os.path.join(pybel_data, DEFAULT_DEFINITION_CACHE_NAME)


class DefinitionCacheManager:
    def __init__(self, conn=None, setup_default_cache=False, log_sql=False):
        """
        :param: conn: custom database connection string'
        :type: str
        :param: setup_cache: Weather or not the namespace namespace_cache should be setted up on initiation.
        :type: bool
        :param: sql_echo: Weather or not echo the running sql code.
        :type: bool
        """
        conn = conn if conn is not None else 'sqlite:///' + DEFAULT_CACHE_LOCATION
        log.info('Loading definition cache from {}'.format(conn))
        start_time = time.time()
        self.eng = create_engine(conn, echo=log_sql)
        self.sesh = scoped_session(sessionmaker(bind=self.eng, autoflush=False, expire_on_commit=False))
        self.namespace_cache = {}
        self.annotation_cache = {}

        self.setup_database()
        if setup_default_cache:
            self.ensure_cache()

        log.info("Initiation of definition cachetook {runtime:3.2f}s".format(runtime=(time.time() - start_time)))

    def __insert_definition(self, definition_url, check_date=True):
        """Inserts namespace and names into namespace namespace_cache db.

        :param definition_url: URL of a namespace or annotation definition file (.belns / .belanno)
        :type definition_url: str
        :param check_date: Indicates if creation dates of namespaces should be checked (outdated namespaces will not be inserted!)
        :type check_date: bool
        """

        def_type = None
        defDict = {
            DEFINITION_NAMESPACE: 'Namespace',
            DEFINITION_ANNOTATION: 'AnnotationDefinition'
        }
        if definition_url.endswith('.belns'):
            def_type = DEFINITION_NAMESPACE
        elif definition_url.endswith('.belanno'):
            def_type = DEFINITION_ANNOTATION

        log.info('Inserting {} {} to definitions cache '.format(defDict[def_type], definition_url))

        def_config = utils.download_url(definition_url)

        def_key = def_config[defDict[def_type]]['Keyword']
        creationDateTime = datetime.strptime(def_config[defDict[def_type]]['CreatedDateTime'], '%Y-%m-%dT%H:%M:%S')
        pubDate = datetime.strptime(def_config['Citation']['PublishedDate'], '%Y-%m-%d') if 'PublishedDate' in \
                                                                                            def_config[
                                                                                                'Citation'] else None

        definition_insert_values = {
            'url': definition_url,
            'definitionType': def_type,
            'author': def_config['Author']['NameString'],
            'keyword': def_key,
            'createdDateTime': creationDateTime,
            'pubDate': pubDate,
            'copyright': def_config['Author']['CopyrightString'],
            'version': def_config[defDict[def_type]]['VersionString'],
            'contact': def_config['Author']['ContactInfoString']
        }

        if def_type == DEFINITION_NAMESPACE:
            self.namespace_cache[definition_url] = dict(def_config['Values'])
        elif def_type == DEFINITION_ANNOTATION:
            self.annotation_cache[definition_url] = dict(def_config['Values'])

        defintion_check = self.check_definition(def_key, def_type)

        if defintion_check:
            definition_old = self.sesh.query(database_models.Definition).filter_by(
                keyword=defintion_check['keyword'],
                createdDateTime=defintion_check['createdDateTime']).first()

            if check_date and not definition_old.createdDateTime < creationDateTime:
                return def_key, definition_old.createdDateTime, None

            else:
                if def_type == DEFINITION_NAMESPACE:
                    self.__insert_definition_helper([definition_insert_values], self.namespace_cache[definition_url])
                elif def_type == DEFINITION_ANNOTATION:
                    self.__insert_definition_helper([definition_insert_values], self.annotation_cache[definition_url])

                return def_key, creationDateTime, definition_old

        if def_type == DEFINITION_NAMESPACE:
            self.__insert_definition_helper([definition_insert_values], self.namespace_cache[definition_url])
        elif def_type == DEFINITION_ANNOTATION:
            self.__insert_definition_helper([definition_insert_values], self.annotation_cache[definition_url])

        return def_key, creationDateTime, None

    def __insert_definition_helper(self, definition_insert_values, contexts_dict):

        definition_entry = self.eng.execute(database_models.Definition.__table__.insert(), definition_insert_values)
        definition_pk = definition_entry.inserted_primary_key[0]

        context_insert_values = [{'definition_id': definition_pk, 'context': name, 'encoding': encoding} for
                                 name, encoding in contexts_dict.items()]

        self.eng.execute(database_models.Context.__table__.insert(), context_insert_values)

    def __cached_definitions(self):
        """Creates the namespace and annotation caches.
        """
        definition_dataframe = pd.read_sql_table(DEFINITION_TABLE_NAME, self.eng)
        context_dataframe = pd.read_sql_table(CONTEXT_TABLE_NAME, self.eng)
        definition_context_dataframe = definition_dataframe.merge(context_dataframe,
                                                                  left_on='id',
                                                                  right_on='definition_id',
                                                                  how='inner')
        grouped_dataframe = definition_context_dataframe[['url', 'context', 'encoding']].groupby("url")

        cache = {url: pd.Series(group.encoding.values, index=group.context).to_dict() for url, group in
                 grouped_dataframe}

        for definition_url in cache:
            if definition_url.endswith('.belns'):
                self.namespace_cache[definition_url] = cache[definition_url]
            elif definition_url.endswith('.belanno'):
                self.annotation_cache[definition_url] = cache[definition_url]

    def setup_database(self, drop_existing=False):
        """Sets the database with the needed tables.

        :param drop_existing: Indicates if exising tables should be dropped and the namespace_cache should be reset.
        :type drop_existing: bool
        """
        start_time = time.time()
        if drop_existing:
            database_models.Base.metadata.drop_all(self.eng)
            log.info("Database was dropped ({runtime:3.2f}sec.)".format(runtime=(time.time() - start_time)))
        database_models.Base.metadata.create_all(self.eng, checkfirst=True)

    def ensure_cache(self, namespace_urls=None, annotation_urls=None):
        """Checks if a namespace namespace_cache already exists in given database and loads the namespace_cache dict.

        :param namespace_urls: List of namespace files by url (.belns files)
        :type namespace_definiton: list
        :param annotation_urls: List of annotation files by url (.belanno files)
        :type annotation_urls: list
        """
        start_time = time.time()
        namespace_urls = namespace_urls if namespace_urls else default_namespaces
        annotation_urls = annotation_urls if annotation_urls else default_annotations

        if self.eng.dialect.has_table(self.eng, DEFINITION_TABLE_NAME):

            for def_type in (DEFINITION_NAMESPACE, DEFINITION_ANNOTATION):

                if not self.sesh.query(database_models.Definition).filter_by(definitionType=def_type).first():
                    if def_type == DEFINITION_NAMESPACE:
                        log.info("Namespace cache is empty, new one is created.")
                        for url in namespace_urls:
                            self.__insert_definition(url, check_date=False)
                    elif def_type == DEFINITION_ANNOTATION:
                        log.info("Annotation cache is empty, new one is created.")
                        for url in annotation_urls:
                            self.__insert_definition(url, check_date=False)

            self.__cached_definitions()

            log.info("Cache setup for namespaces and annotations done! ({runtime:3.2f}sec.)".format(
                runtime=(time.time() - start_time)))
        else:
            self.setup_database()
            self.ensure_cache(namespace_urls, annotation_urls)
            log.info("New database is setup and caches were created! ({runtime:3.2f}sec.)".format(
                runtime=(time.time() - start_time)))

    def update_definition_cache(self, namespace_urls=None, annotation_urls=None, overwrite_old_definitions=True):
        """Updates the cache DB with given namespace and annotation list (see defaults.py)

        :param namespace_urls: List of namespace files by url (.belns files)
        :type namespace_urls: list
        :param annotation_urls: List of namespaces files by url (.belanno files)
        :type annotation_urls: list
        :param overwrite_old_definitions: Indicates if outdated namespaces or annotations should be overwritten
        :type overwrite_old_definitions: bool
        """
        namespace_urls = namespace_urls if namespace_urls is not None else default_namespaces
        annotation_urls = annotation_urls if annotation_urls is not None else default_annotations

        if self.eng.dialect.has_table(self.eng, DEFINITION_TABLE_NAME):
            for url in namespace_urls + annotation_urls:
                self.update_definition(url, overwrite_old_definitions)

        else:
            self.setup_database()
            self.update_definition_cache(namespace_urls, annotation_urls, overwrite_old_definitions)

    def update_definition(self, definition_url, overwrite_old_definition=True):
        """Checks if a namespace or annotation that is given by url is already in cache and if so, if it is up to date.
        
        :param definition_url: URL to a namespace or annotation definition file (.belns / .belanno)
        :type definition_url: str
        :param overwrite_old_definition: Indicates if old namespaces should be removed from namespace_cache if a new version is inersted.
        :type overwrite_old_definition: bool
        """
        start_time = time.time()

        if self.sesh.query(exists().where(database_models.Definition.url == definition_url)).scalar():
            if not self.namespace_cache or not self.annotation_cache:
                self.ensure_cache()
            return

        definition_key, creationDateTime, definition_old = self.__insert_definition(definition_url,
                                                                                    check_date=overwrite_old_definition)

        if definition_old and overwrite_old_definition and definition_old.createdDateTime < creationDateTime:
            log.warning(
                "Old definition '{def_key}' [{def_old_url}] will be removed from cache database due to updated version [{def_new_url}]".format(
                    def_key=definition_old.keyword,
                    def_old_url=definition_old.url,
                    def_new_url=definition_url))
            old_dateTime = definition_old.createdDateTime
            self.remove_definition(definition_old.url, definition_old.createdDateTime)

            log.info(
                "'{definition_keyword}' was updated from v.{version_old} to v.{version_new} ({runtime:3.2f}sec.)".format(
                    definition_keyword=definition_key,
                    version_old=old_dateTime,
                    version_new=creationDateTime,
                    runtime=time.time() - start_time))

    def check_definition(self, definition_key, definition_type):
        """Check if namespace exists and what version is in the namespace_cache.

        :param namesapce_key: Keyword for a namespace or annotation. i.e.: 'HGNC' or 'Anatomy'
        :type definition_key: str ('N' for Namespace or 'A' for Annotation)
        :return: None (does not exist) or number of namesapces.
        :rtype: None or dict
        """
        definition_old = self.sesh.query(database_models.Definition).filter_by(keyword=definition_key,
                                                                               definitionType=definition_type).first()
        if definition_old:
            return {
                'keyword': definition_old.keyword,
                'version': definition_old.version,
                'url': definition_old.url,
                'createdDateTime': definition_old.createdDateTime,
                'pubDate': definition_old.pubDate,
                'copyright': definition_old.copyright,
                'author': definition_old.author,
                'contact': definition_old.contact
            }

    def remove_definition(self, definition_url, created_date_time):
        """Removes namespace or annotation from cache by url and createdDateTime.

        :param definition_url: URL to a namespace or annotation definition file (.belns / .belanno)
        :type definition_url: str
        :param created_date_time: Date and time for creation (createdDateTime) in the definition file.
        format like: 2015-06-11T19:51:19
        :type created_date_time: str

        """
        def_to_remove = created_date_time if isinstance(created_date_time, datetime) else datetime.strptime(
            created_date_time, '%Y-%m-%dT%H:%M:%S')
        definition = self.sesh.query(database_models.Definition).filter_by(url=definition_url,
                                                                           createdDateTime=def_to_remove).first()
        if definition:
            definition_type = definition.definitionType
            self.sesh.delete(definition)
            self.sesh.commit()
            if definition_type == DEFINITION_NAMESPACE:
                del self.namespace_cache[definition_url]
            elif definition_type == DEFINITION_ANNOTATION:
                del self.annotation_cache[definition_url]
