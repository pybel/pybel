import logging
import os
import time
from datetime import datetime

import networkx as nx
import pandas as pd
from sqlalchemy import create_engine, exists
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound

from . import models
from .defaults import default_namespaces, default_annotations, default_owl
from .models import DEFINITION_TABLE_NAME, DEFINITION_ENTRY_TABLE_NAME, DEFINITION_ANNOTATION, DEFINITION_NAMESPACE
from .utils import parse_owl
from ..constants import PYBEL_DATA
from ..utils import download_url

log = logging.getLogger('pybel')

DEFAULT_DEFINITION_CACHE_NAME = 'definitions.db'
DEFAULT_CACHE_LOCATION = os.path.join(PYBEL_DATA, DEFAULT_DEFINITION_CACHE_NAME)

CREATION_DATE_FMT = '%Y-%m-%dT%H:%M:%S'
PUBLISHED_DATE_FMT = '%Y-%m-%d'

# TODO make Enum
definition_headers = {
    DEFINITION_NAMESPACE: 'Namespace',
    DEFINITION_ANNOTATION: 'AnnotationDefinition'
}

VALID_NAMESPACE_DOMAINSTRING = {"BiologicalProcess", "Chemical", "Gene and Gene Products", "Other"}


def parse_datetime(s):
    try:
        dt = datetime.strptime(s, CREATION_DATE_FMT)
        return dt
    except:
        try:
            dt = datetime.strptime(s, PUBLISHED_DATE_FMT)
            return dt
        except:
            raise ValueError('Incorrect datetime format for {}'.format(s))


class BaseCacheManager:
    def __init__(self, connection=None, echo=False, create_all=False):
        connection = connection if connection is not None else 'sqlite:///' + DEFAULT_CACHE_LOCATION
        self.engine = create_engine(connection, echo=echo)
        self.session = scoped_session(sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False))

        if create_all:
            self.create_database()

    def create_database(self):
        models.Base.metadata.create_all(self.engine)

    def drop_database(self):
        models.Base.metadata.drop_all(self.engine)


class CacheManager(BaseCacheManager):
    def __init__(self, connection=None, create_all=False, setup_default_cache=False, echo=False):
        """The definition cache manager takes care of storing BEL namespace and annotation files for later use.
        It uses SQLite by default for speed and lightness, but any database can be used wiht its SQLAlchemy interface.

        :param: conn: custom database connection string
        :type conn: str
        :param create_all: create database?
        :type create_all: bool
        :param: setup_default_cache: Whether or not the definition cache should be set up on initiation.
        :type setup_default_cache: bool
        :param: echo: Whether or not echo the running sql code.
        :type echo: bool
        """

        BaseCacheManager.__init__(self, connection=connection, echo=echo, create_all=create_all)

        # Normal cache management
        self.namespace_cache = {}
        self.annotation_cache = {}

        # Owl Cache Management
        # TODO harmonize term cache with namespace cache
        self.term_cache = {}
        self.edge_cache = {}
        self.graph_cache = {}

        self.setup_database()

        if setup_default_cache:
            self.ensure_cache()

    def insert_definition(self, definition_url, check_date=True):
        """Inserts namespace and names into namespace namespace_cache db.

        :param definition_url: URL of a namespace or annotation definition file (.belns / .belanno)
        :type definition_url: str
        :param check_date: Indicates if creation dates of namespaces should be checked
                            (outdated namespaces will not be inserted!)
        :type check_date: bool
        """

        if definition_url.endswith('.belns'):
            def_type = DEFINITION_NAMESPACE
        elif definition_url.endswith('.belanno'):
            def_type = DEFINITION_ANNOTATION
        else:
            raise ValueError('Definition URL has invalid extension: {}'.format(definition_url))

        log.info('Caching %s %s', definition_headers[def_type], definition_url)

        config = download_url(definition_url)

        defDictType = config[definition_headers[def_type]]

        def_key = defDictType['Keyword']

        try:
            creation_date_time = datetime.strptime(defDictType['CreatedDateTime'], CREATION_DATE_FMT)
        except:
            raise ValueError('Incorrect format for datetime: {}'.format(defDictType['CreatedDateTime']))

        pub_date = None
        if 'PublishedDate' in config['Citation']:
            try:
                pub_date = datetime.strptime(config['Citation']['PublishedDate'], PUBLISHED_DATE_FMT)
            except:
                try:
                    pub_date = datetime.strptime(config['Citation']['PublishedDate'], CREATION_DATE_FMT)
                except:
                    raise ValueError(
                        "Incorrect format for datetime: {}".format(config['Citation']['PublishedDate']))

        definition_insert_values = {
            'url': definition_url,
            'definitionType': def_type,
            'author': config['Author']['NameString'],
            'keyword': def_key,
            'createdDateTime': creation_date_time,
            'pubDate': pub_date,
            'copyright': config['Author']['CopyrightString'],
            'version': config[definition_headers[def_type]]['VersionString'],
            'contact': config['Author']['ContactInfoString']
        }

        if def_type == DEFINITION_NAMESPACE:
            self.namespace_cache[definition_url] = dict(config['Values'])
        elif def_type == DEFINITION_ANNOTATION:
            self.annotation_cache[definition_url] = dict(config['Values'])

        definition_check = self.check_definition(def_key, def_type)

        if definition_check:
            definition_old = self.session.query(models.Definition).filter_by(
                keyword=definition_check['keyword'],
                createdDateTime=definition_check['createdDateTime']).first()

            if check_date and not definition_old.createdDateTime < creation_date_time:
                return def_key, definition_old.createdDateTime, None

            else:
                if def_type == DEFINITION_NAMESPACE:
                    self.__insert_definition_helper([definition_insert_values], self.namespace_cache[definition_url])
                elif def_type == DEFINITION_ANNOTATION:
                    self.__insert_definition_helper([definition_insert_values], self.annotation_cache[definition_url])

                return def_key, creation_date_time, definition_old

        if def_type == DEFINITION_NAMESPACE:
            self.__insert_definition_helper([definition_insert_values], self.namespace_cache[definition_url])
        elif def_type == DEFINITION_ANNOTATION:
            self.__insert_definition_helper([definition_insert_values], self.annotation_cache[definition_url])

        return def_key, creation_date_time, None

    def __insert_definition_helper(self, definition_insert_values, contexts_dict):

        definition_entry = self.engine.execute(models.Definition.__table__.insert(), definition_insert_values)
        definition_pk = definition_entry.inserted_primary_key[0]

        context_insert_values = [{'definition_id': definition_pk, 'context': name, 'encoding': encoding} for
                                 name, encoding in contexts_dict.items()]

        self.engine.execute(models.Entry.__table__.insert(), context_insert_values)

    def __cached_definitions(self):
        """Creates the namespace and annotation caches"""
        definition_dataframe = pd.read_sql_table(DEFINITION_TABLE_NAME, self.engine)
        context_dataframe = pd.read_sql_table(DEFINITION_ENTRY_TABLE_NAME, self.engine)
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

        :param drop_existing: Indicates if existing tables should be dropped and the namespace_cache should be reset.
        :type drop_existing: bool
        """
        start_time = time.time()
        if drop_existing:
            models.Base.metadata.drop_all(self.engine)
            log.info("Database was dropped in %3.2fs", time.time() - start_time)
        models.Base.metadata.create_all(self.engine, checkfirst=True)

    def ensure_cache(self, namespace_urls=None, annotation_urls=None):
        """Checks if a namespace namespace_cache already exists in given database and loads the namespace_cache dict.

        :param namespace_urls: List of namespace files by url (.belns files)
        :type namespace_definiton: list
        :param annotation_urls: List of annotation files by url (.belanno files)
        :type annotation_urls: list
        """
        namespace_urls = namespace_urls if namespace_urls else default_namespaces
        annotation_urls = annotation_urls if annotation_urls else default_annotations

        if self.engine.dialect.has_table(self.engine, DEFINITION_TABLE_NAME):

            for def_type in (DEFINITION_NAMESPACE, DEFINITION_ANNOTATION):

                if not self.session.query(models.Definition).filter_by(definitionType=def_type).first():
                    if def_type == DEFINITION_NAMESPACE:
                        log.info("Namespace cache is empty, new one is created.")
                        for url in namespace_urls:
                            self.insert_definition(url, check_date=False)
                    elif def_type == DEFINITION_ANNOTATION:
                        log.info("Annotation cache is empty, new one is created.")
                        for url in annotation_urls:
                            self.insert_definition(url, check_date=False)

            self.__cached_definitions()

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

        if self.engine.dialect.has_table(self.engine, DEFINITION_TABLE_NAME):
            for url in namespace_urls + annotation_urls:
                self.update_definition(url, overwrite_old_definitions)

    def update_definition(self, definition_url, overwrite_old_definition=True):
        """Checks if a namespace or annotation that is given by url is already in cache and if so, if it is up to date.
        
        :param definition_url: URL to a namespace or annotation definition file (.belns / .belanno)
        :type definition_url: str
        :param overwrite_old_definition: Indicates if old namespaces should be removed from namespace_cache
                                            if a new version is inersted.
        :type overwrite_old_definition: bool
        """
        start_time = time.time()

        if self.session.query(exists().where(models.Definition.url == definition_url)).scalar():
            if not self.namespace_cache or not self.annotation_cache:
                self.ensure_cache()
            return

        definition_key, creationDateTime, definition_old = self.insert_definition(definition_url,
                                                                                  check_date=overwrite_old_definition)

        if definition_old and overwrite_old_definition and definition_old.createdDateTime < creationDateTime:
            log.warning(
                "Old definition %s [%s] will be removed from cache database due to updated version [%s]",
                definition_old.keyword,
                definition_old.url,
                definition_url
            )
            old_dateTime = definition_old.createdDateTime
            self.remove_definition(definition_old.url, definition_old.createdDateTime)

            log.info(
                "%s was updated from v.%s to v.%s in %3.2fs",
                definition_key,
                old_dateTime,
                creationDateTime,
                time.time() - start_time
            )

    def check_definition(self, definition_key, definition_type):
        """Check if namespace exists and what version is in the namespace_cache.

        :param namesapce_key: Keyword for a namespace or annotation. i.e.: 'HGNC' or 'Anatomy'
        :type definition_key: str ('N' for Namespace or 'A' for Annotation)
        :return: None (does not exist) or number of namesapces.
        :rtype: None or dict
        """
        definition_old = self.session.query(models.Definition).filter_by(keyword=definition_key,
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
            created_date_time, CREATION_DATE_FMT)
        definition = self.session.query(models.Definition).filter_by(url=definition_url,
                                                                     createdDateTime=def_to_remove).first()
        if definition:
            definition_type = definition.definitionType
            self.session.delete(definition)
            self.session.commit()
            if definition_type == DEFINITION_NAMESPACE:
                del self.namespace_cache[definition_url]
            elif definition_type == DEFINITION_ANNOTATION:
                del self.annotation_cache[definition_url]

    #######################################################

    def insert_definition_cth(self, url, definition_type):
        """
        :param url:
        :param definition_type: either DEFINITION_NAMESPACE or DEFINITION_ANNOTATION
        :return: SQL Alchemy model instance, populated with data from URL
        """
        config = download_url(url)

        header = definition_headers[definition_type]

        definition_insert_values = {
            'url': url,
            'definitionType': definition_type,
            'author': config['Author']['NameString'],
            'keyword': config[header]['Keyword'],
            'createdDateTime': parse_datetime(config[header]['CreatedDateTime']),
            'copyright': config['Author']['CopyrightString'],
            'version': config[header]['VersionString'],
            'contact': config['Author']['ContactInfoString']
        }

        if 'PublishedDate' in config['Citation']:
            definition_insert_values['pubDate'] = parse_datetime(config['Citation']['PublishedDate'])

        definition = models.Definition(**definition_insert_values)
        definition.entries = [models.Entry(context=c, encoding=e) for c, e in config['Values'].items() if c]

        self.session.add(definition)
        self.session.commit()

        return definition

    def ensure_namespace(self, url):
        if url in self.namespace_cache:
            return

        try:
            results = self.session.query(models.Definition).filter(models.Definition.url == url).one()
        except NoResultFound:

            # TODO split namespace and annotation handling
            # if config[header]['DomainString'] not in VALID_NAMESPACE_DOMAINSTRING:
            #    raise ValueError("Invalid DomainString {}".format(config[header]['DomainString']))

            results = self.insert_definition_cth(url, DEFINITION_NAMESPACE)

        if results is None:
            raise ValueError('No results for {}'.format(url))
        elif not results.entries:
            raise ValueError('No context for {}'.format(url))

        self.namespace_cache[url] = {context.context: set(context.encoding) for context in results.entries}

    def ensure_annotation(self, url):
        if url in self.annotation_cache:
            return

        try:
            results = self.session.query(models.Definition).filter(models.Definition.url == url).one()
        except NoResultFound:
            results = self.insert_definition_cth(url, DEFINITION_ANNOTATION)

        self.annotation_cache[url] = {context.context: context.encoding for context in results.entries}

    def get_belns(self, url):
        self.ensure_namespace(url)
        return self.namespace_cache[url]

    def get_belanno(self, url):
        self.ensure_annotation(url)
        return self.annotation_cache[url]

    def ls(self):
        return [definition.url for definition in self.session.query(models.Definition).all()]

    def ls_definition(self, definition_url):
        definition = self.session.query(models.Definition).filter_by(url=definition_url).first()
        return [context.context for context in definition.contexts]

    def ensure_owl(self, iri):
        if iri in self.term_cache:
            return
        try:
            results = self.session.query(models.Owl).filter(models.Owl.iri == iri).one()
        except NoResultFound:
            results = self.insert_by_iri(iri)

        self.term_cache[iri] = set(entry.entry for entry in results.entries)
        self.edge_cache[iri] = set((sub.entry, sup.entry) for sub in results.entries for sup in sub.children)

        graph = nx.DiGraph()
        graph.add_edges_from(self.edge_cache[iri])
        self.graph_cache[iri] = graph

    def get_owl_terms(self, iri):
        self.ensure_owl(iri)
        return self.term_cache[iri]

    def load_default_owl(self):
        for url in default_owl:
            self.insert_by_iri(url)

    def ls_owl(self):
        return [owl.iri for owl in self.session.query(models.Owl).all()]

    def ls_owl_definition(self, iri):
        res = self.session.query(models.Owl).filter(models.Owl.iri == iri).one()
        log.info('Load OWL %s from cache', res)
        return [entry.entry for entry in res.entries]

    def insert_by_iri(self, iri):
        return self.insert_by_graph(iri, parse_owl(iri))

    def insert_by_graph(self, iri, graph):
        if 0 < self.session.query(models.Owl).filter(models.Owl.iri == iri).count():
            log.debug('%s already cached', iri)
            return

        owl = models.Owl(iri=iri)

        entries = {node: models.OwlEntry(entry=node) for node in graph.nodes_iter()}

        owl.entries = list(entries.values())

        for u, v in graph.edges_iter():
            entries[u].children.append(entries[v])

        self.session.add(owl)
        self.session.commit()

        return owl

    def get_edges(self, iri):
        self.ensure_owl(iri)
        return self.edge_cache[iri]

    def get_graph(self, iri):
        self.ensure_owl(iri)
        return self.graph_cache[iri]
