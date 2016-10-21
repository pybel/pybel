from . import database_models
from .. import utils
import time
import logging
import pandas as pd

from .defaults import default_namespaces
from configparser import ConfigParser
from datetime import datetime
from sqlalchemy import create_engine, exists
from sqlalchemy.orm import sessionmaker, scoped_session

log = logging.getLogger('pybel')

class NamespaceCache:
    
    def __init__(self, database_string='sqlite:///namespaceCache.db', setup_default_cache=False, sql_echo=False):
        """
        :param: database_string: Database connection
        :type: str
        :param: setup_cache: Weather or not the namespace cache should be setted up on initiation.
        :type: bool
        :param: sql_echo: Weather or not echo the running sql code.
        :type: bool
        """
        start_time = time.time()
        self.__db_engine = create_engine(database_string,echo=sql_echo)
        self.__db_session = scoped_session(sessionmaker(bind=self.__db_engine,autoflush=False,expire_on_commit=False))
        self.cache = {}
        
        if setup_default_cache:
            self.setup_namespace_cache()
            
        log.info("Initiation of NamespaceCache done ({runtime:3.2f})".format(runtime=(time.time()-start_time)))
    
    def setup_database(self, drop_existing=False):
        """
        :param: drop_existing: Indicades if exising tables should be dropped and the cache should be resetted.
        
        Sets the database with the needed tables.
        """
        start_time = time.time()
        if drop_existing:
            database_models.Base.metadata.drop_all(self.__db_engine)
            log.info("Database was dropped! ({runtime:3.2f}sec.)".format(runtime=(time.time()-start_time)))
        database_models.Base.metadata.create_all(self.__db_engine, checkfirst=True)
    
    def setup_namespace_cache(self, namespace_definition=default_namespaces):
        """
        Checks if a namespace cache allready exists in given database and loads the namespace_cache dict.
        """
        start_time = time.time()
        if self.__db_engine.dialect.has_table(self.__db_engine, 'pybelcache_namespace'):
            
            if self.__db_session.query(database_models.Namespace).first():
                self.__cached_namespaces()
                log.info("Namespace cache allready exists and is loaded from database ({runtime:3.2f}sec.)".format(runtime=(time.time()-start_time)))
            else:
                self.insert_namespaces(namespace_definition)
                log.info("Database allready exists and namespace cache gets created ({runtime:3.2f}sec.)".format(runtime=(time.time()-start_time)))
        
        else:
            self.setup_database()
            self.setup_namespace_cache(namespace_definition)
            log.info("New database is setup and cache was created! ({runtime:3.2f})".format(runtime=(time.time()-start_time)))
    
    def insert_namespaces(self, namespace_definition):
        """
        Inserts latest BEL namespaces to the database.
        """
        default_url = namespace_definition['url']
        url = default_url if default_url.endswith("/") else default_url+"/" 
        for namespace in namespace_definition['namespaces']:
            self.__insert_namespace("{}{}".format(url,namespace))
    
    def update_namespace_cache(self, namespace_definition=default_namespaces, remove_old_namespaces=True):
        """
        Updates the namespace cache DB with given namespace definition dictionary (see defaults.py)
        """
        start_time = time.time()        
        namespace_model = database_models.Namespace
        default_url = namespace_definition['url']
        url = default_url if default_url.endswith("/") else default_url+"/"
        
        if self.__db_engine.dialect.has_table(self.__db_engine, 'pybelcache_namespace'):
            default_url = namespace_definition['url']
            url = default_url if default_url.endswith("/") else default_url+"/"
            for namespace in namespace_definition['namespaces']:
                self.update_namespace(url+namespace, remove_old_namespaces)
        
        else:
            self.setup_database()
            self.update_namespace_cache(namespace_definition, remove_old_namespaces)
    
    def update_namespace(self, namespace_url, remove_old_namespace=True):
        """
        Checks if a namespace that is given by url is already in namespace cache and if so, if it is up to date.
        Works for urls like: http://resource.belframework.org/belframework/20150611/namespace/
        """
        start_time = time.time()        
        namespace_model = database_models.Namespace
        
        namespace_url_existing = self.__db_session.query(exists().where(namespace_model.url==namespace_url)).scalar()
        
        if not namespace_url_existing:            
            namespace_key, creationDateTime, namespace_old = self.__insert_namespace(namespace_url)
            
            if namespace_old and remove_old_namespace and namespace_old.createdDateTime < creationDateTime:
                log.warning("Old namespace '{ns_key}' [{ns_old_url}] will be removed from cache database due to updated version [{ns_new_url}]".format(ns_key=namespace_old.keyword,
                                                                                                                                                       ns_old_url=namespace_old.url,
                                                                                                                                                       ns_new_url=namespace_url))
                old_dateTime = namespace_old.createdDateTime
                self.remove_namespace(namespace_old.url,namespace_old.createdDateTime)

                log.info("'{namespace_keyword}' was updated from v.{version_old} to v.{version_new} ({runtime:3.2f}sec.)".format(namespace_keyword=namespace_key, 
                                                                                                                                 version_old=old_dateTime, 
                                                                                                                                 version_new=creationDateTime,
                                                                                                                                 runtime=time.time()-start_time))
    
    def check_namespace(self, namespace_key):
        """
        :param: namesapce_key: Keyword for a namespace. i.e.: 'HGNC'
        :type: str
        
        Check if namespace exists and what version is in the cache.
        
        :return: None (doese not exist) or number of namesapces.
        """
        namespace_info = None
        namespace_model = database_models.Namespace
        namespace_old = self.__db_session.query(namespace_model).filter_by(keyword=namespace_key).first()
        if namespace_old:
            namespace_info = {'keyword':namespace_old.keyword,
                              'version':namespace_old.version,
                              'url':namespace_old.url,
                              'createdDateTime':namespace_old.createdDateTime,
                              'pubDate':namespace_old.pubDate,
                              'copyright':namespace_old.copyright,
                              'author':namespace_old.author,
                              'contact':namespace_old.contact}
         
        return namespace_info
 
    def remove_namespace(self, namespace_url, createdDateTime):
        """
        Removes namespace from cache by url.
        """
        start_time = time.time()
        namespace = self.__db_session.query(database_models.Namespace).filter_by(url=namespace_url,createdDateTime=createdDateTime).first()
        if namespace:
            self.__db_session.delete(namespace)
            self.__db_session.commit()
            del(self.cache[namespace_url])
            
            log.info("Namespace '{ns_key}' [{ns_url}] was removed from cache DB! ({runtime:3.2f}sec.)".format(ns_key=namespace.keyword,
                                                                                                              ns_url=namespace.url,
                                                                                                              runtime=(time.time()-start_time)))
            
    def __insert_namespace(self, namespace_url):
        """
        :param: namespace_url: URL of the namespace definition file (.belns)
        
        Inserts namespace and names into namespace cache db.
        """
        tmp_time = time.time()
        namespace_insert_values = []
        name_insert_values = []
        namespace_old = None
        namespace_model = database_models.Namespace
        
        ns_config = utils.download_url(namespace_url)
        
        namespace_key = ns_config['Namespace']['Keyword']
        creationDateTime = datetime.strptime(ns_config['Namespace']['CreatedDateTime'],'%Y-%m-%dT%H:%M:%S')
        
        namespace_insert_values = [{'url':namespace_url,
                                    'author':ns_config['Author']['NameString'],
                                    'keyword':namespace_key,
                                    'createdDateTime':creationDateTime,
                                    'pubDate':datetime.strptime(ns_config['Citation']['PublishedDate'],'%Y-%m-%d') if 'PublishedDate' in ns_config['Citation'] else None,
                                    'copyright':ns_config['Author']['CopyrightString'],
                                    'version':ns_config['Namespace']['VersionString'],
                                    'contact':ns_config['Author']['ContactInfoString']}]
                    
        namespace_check = self.check_namespace(namespace_key) 
        
        if namespace_check:
            namespace_old = self.__db_session.query(namespace_model).filter_by(keyword=namespace_check['keyword'],version=namespace_check['version']).first()
     
        if not namespace_check or (namespace_old and namespace_old.createdDateTime < creationDateTime):
        
            namespace_entry = self.__db_engine.execute(namespace_model.__table__.insert(),namespace_insert_values)
            namespace_pk = namespace_entry.inserted_primary_key[0]
            
            names_dict = dict(ns_config['Values'])
            self.cache[namespace_url] = dict(ns_config['Values'])
            
            name_insert_values = [{'namespace_id':namespace_pk,'name':name_info[0],'encoding':name_info[1]} for name_info in names_dict.items()]
            
            self.__db_engine.execute(database_models.Namespace_Name.__table__.insert(),name_insert_values)
            
            log.info("Cached namespace '{ns_key}' [{url}] ({runtime:3.2f}sec.)".format(ns_key=namespace_key, url=namespace_url, runtime=(time.time()-tmp_time)))
        
        else:
            creationDateTime = namespace_old.createdDateTime
            namespace_old = None
        
        return (namespace_key, creationDateTime, namespace_old)
    
    def __cached_namespaces(self):
        """
        Returns the cached namespaces as dictionary.
        """
        start_time = time.time()
        
        namespace_dataframe = pd.read_sql_table('pybelcache_namespace',self.__db_engine)
        name_dataframe = pd.read_sql_table('pybelcache_name', self.__db_engine)
        namespaces_names_dataframe = namespace_dataframe.merge(name_dataframe, left_on='id', right_on='namespace_id', how='inner')
        grouped_dataframe = namespaces_names_dataframe[['url','name','encoding']].groupby("url") 
        self.cache = {keyword:pd.Series(group.encoding.values,index=group.name).to_dict() for keyword,group in grouped_dataframe}
        