import unittest
import os

dir_path = os.path.dirname(os.path.realpath(__file__))

from pybel.manager.namespacecache import NamespaceCache
from datetime import datetime

class TestNsCache(unittest.TestCase):
    
    def test_setup(self):
        
        test_db_string = 'sqlite://'
        
        expected_check = {'keyword':'CHEBIID',
                          'version':'20150611',
                          'url':'http://resource.belframework.org/belframework/20150611/namespace/chebi-ids.belns',
                          'createdDateTime':datetime(2015, 6, 11, 19, 51, 16),
                          'pubDate':datetime(2015, 6, 1, 0, 0),
                          'copyright':'Copyright (c) 2015, OpenBEL Project. This work is licensed under a Creative Commons Attribution 3.0 Unported License.',
                          'author':'OpenBEL',
                          'contact':'info@openbel.org'}
        
        expected_keys = ['http://resource.belframework.org/belframework/20150611/namespace/mesh-cellular-structures-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/chebi.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/hgnc-human-genes.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/disease-ontology-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/selventa-protein-families.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/affy-probeset-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/go-biological-process.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/go-cellular-component-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/mesh-diseases-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/disease-ontology.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/mesh-chemicals.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/mesh-cellular-structures.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/go-cellular-component.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/selventa-legacy-chemicals.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/swissprot.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/rgd-rat-genes.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/mesh-processes.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/selventa-named-complexes.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/chebi-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/entrez-gene-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/mesh-diseases.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/mesh-chemicals-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/swissprot-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/selventa-legacy-diseases.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/go-biological-process-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/mesh-processes-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/mgi-mouse-genes.belns']

        
        test_db = NamespaceCache(test_db_string, setup_default_cache=True)
        test_db_keys = test_db.cache.keys()
        for db_key in expected_keys:
            self.assertTrue(db_key in test_db_keys)
        
        app_in_hgnc = 'APP' in test_db.cache['http://resource.belframework.org/belframework/20150611/namespace/hgnc-human-genes.belns']
        self.assertTrue(app_in_hgnc)
        
        test_db.setup_namespace_cache() 
        test_db_keys = test_db.cache.keys()
        for db_key in expected_keys:  
            self.assertTrue(db_key in test_db_keys)
        
        fake_key = 'http://resource.belframework.org/belframework/20150611/namespace/chebi-ids.belns341'
        self.assertFalse(fake_key in test_db_keys)
        
    def test_allreadyIn(self):
        
        test_db_string = 'sqlite://'
        
        data_url = os.path.join(dir_path,'bel')
        
        test_namespace = {'url':'file://'+data_url,
                          'namespaces':['test_ns_1.belns']}
        
        test_db = NamespaceCache(test_db_string)
        test_db.setup_database()
        
        for namespace in test_namespace['namespaces']:
            namespace_exists = test_db.check_namespace("{}{}".format(test_namespace['url'],namespace))
            self.assertIsNone(namespace_exists)
    
    def test_importing(self):
        
        test_db_string = 'sqlite://'
        
        data_url = os.path.join(dir_path,'bel')
        
        test_namespace = {'url':'file://'+data_url,
                          'namespaces':['test_ns_1.belns']}
    
        expected_cache_dict = {'file://'+data_url+"/test_ns_1.belns":{'TestValue1':'O',
                                                                      'TestValue2':'O',
                                                                      'TestValue3':'O',
                                                                      'TestValue4':'O',
                                                                      'TestValue5':'O'}}
        
        expected_result = {'keyword':'TESTNS1',
                              'version':'1.0.0',
                              'url':'file://'+os.path.join(dir_path,'bel','test_ns_1.belns'),
                              'createdDateTime':datetime(2016, 9, 17, 20, 50),
                              'pubDate':None,
                              'copyright':'Copyright (c) Charles Tapley Hoyt. All Rights Reserved.',
                              'author':'Charles Tapley Hoyt',
                              'contact':'charles.hoyt@scai.fraunhofer.de'}
        
        test_db = NamespaceCache(test_db_string)
        test_db.setup_database(drop_existing=True)
        test_db.setup_namespace_cache(test_namespace)

        self.assertEqual(expected_cache_dict, test_db.cache)
        
        check_result = test_db.check_namespace('TESTNS1')
        self.assertEqual(expected_result, check_result)
        
    
    def test_delete(self):
        
        test_db_string = 'sqlite://'
        
        data_url = os.path.join(dir_path,'bel')
        
        test_namespace = {'url':'file://'+data_url,
                          'namespaces':['test_ns_1.belns']}
    
        expected_cache_dict = {'file://'+data_url+"/test_ns_1.belns":{'TestValue1':'O',
                                                                      'TestValue2':'O',
                                                                      'TestValue3':'O',
                                                                      'TestValue4':'O',
                                                                      'TestValue5':'O'}}
        
        test_db = NamespaceCache(test_db_string)
        test_db.setup_database(drop_existing=True)
        test_db.setup_namespace_cache(test_namespace)
        
        check_result_before = test_db.check_namespace("TESTNS1")
        self.assertIsNotNone(check_result_before)
        
        test_db.remove_namespace('file://'+data_url+"/test_ns_1.belns",datetime(2016, 9, 17, 20, 50))
        
        check_result = test_db.check_namespace("TESTNS1")        
        self.assertIsNone(check_result)
    
    def test_update_namespace(self):
        
        test_db_string = 'sqlite://'
        
        data_url = os.path.join(dir_path,'bel')
        
        test_namespace = {'url':'file://'+data_url,
                          'namespaces':['test_ns_1.belns']}
    
        expected_cache_dict1 = {'file://'+data_url+"/test_ns_1.belns":{'TestValue1':'O',
                                                                      'TestValue2':'O',
                                                                      'TestValue3':'O',
                                                                      'TestValue4':'O',
                                                                      'TestValue5':'O'}}
        
        expected_cache_dict2 = {'file://'+data_url+"/test_ns_1.belns":{'TestValue1':'O',
                                                                      'TestValue2':'O',
                                                                      'TestValue3':'O',
                                                                      'TestValue4':'O',
                                                                      'TestValue5':'O'},
                                'file://'+data_url+"/test_ns_1_updated.belns":{'ImprovedTestValue1':'O',
                                                                      'TestValue2':'O',
                                                                      'TestValue3':'O',
                                                                      'ImprovedTestValue4':'O',
                                                                      'TestValue5':'O',
                                                                      'AdditionalValue6':'O'}}
        
        expected_cache_dict3 = {'file://'+data_url+"/test_ns_1_updated.belns":{'ImprovedTestValue1':'O',
                                                                      'TestValue2':'O',
                                                                      'TestValue3':'O',
                                                                      'ImprovedTestValue4':'O',
                                                                      'TestValue5':'O',
                                                                      'AdditionalValue6':'O'}}
        
        test_db = NamespaceCache(test_db_string)
        test_db.setup_database(drop_existing=True)
        test_db.setup_namespace_cache(test_namespace)
        
        check_result_before = test_db.check_namespace("TESTNS1")
        self.assertIsNotNone(check_result_before)
        self.assertEqual(expected_cache_dict1, test_db.cache)
        self.assertNotEqual(expected_cache_dict2, test_db.cache)
        self.assertNotEqual(expected_cache_dict3, test_db.cache)
        
        test_db.update_namespace('file://'+data_url+"/test_ns_1_updated.belns", remove_old_namespace=False)
        self.assertNotEqual(expected_cache_dict1, test_db.cache)
        self.assertEqual(expected_cache_dict2, test_db.cache)
        self.assertNotEqual(expected_cache_dict3, test_db.cache)
        
        test_db2 = NamespaceCache(test_db_string)
        test_db2.setup_database(drop_existing=True)
        test_db2.setup_namespace_cache(test_namespace)
        
        check_result_before2 = test_db2.check_namespace("TESTNS1")
        self.assertIsNotNone(check_result_before2)
        
        test_db2.update_namespace('file://'+data_url+"/test_ns_1_updated.belns", remove_old_namespace=True)
        self.assertNotEqual(expected_cache_dict1, test_db2.cache)
        self.assertNotEqual(expected_cache_dict2, test_db2.cache)
        self.assertEqual(expected_cache_dict3, test_db2.cache)
        
    def test_update_namespaceCache(self):
        
        test_db_string = 'sqlite://'
        
        expected_keys = ['http://resource.belframework.org/belframework/20150611/namespace/mesh-cellular-structures-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/chebi.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/hgnc-human-genes.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/disease-ontology-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/selventa-protein-families.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/affy-probeset-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/go-biological-process.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/go-cellular-component-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/mesh-diseases-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/disease-ontology.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/mesh-chemicals.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/mesh-cellular-structures.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/go-cellular-component.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/selventa-legacy-chemicals.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/swissprot.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/rgd-rat-genes.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/mesh-processes.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/selventa-named-complexes.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/chebi-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/entrez-gene-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/mesh-diseases.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/mesh-chemicals-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/swissprot-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/selventa-legacy-diseases.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/go-biological-process-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/mesh-processes-ids.belns',
                         'http://resource.belframework.org/belframework/20150611/namespace/mgi-mouse-genes.belns']
        
        test_db = NamespaceCache(test_db_string)
        test_db.update_namespace_cache()
        test_db_keys = test_db.cache.keys()
        for db_key in expected_keys:
            self.assertTrue(db_key in test_db_keys)
        
        ns_removed = 'http://resource.belframework.org/belframework/20150611/namespace/hgnc-human-genes.belns'
        ns_to_add = 'http://resource.belframework.org/belframework/20131211/namespace/hgnc-human-genes.belns'
        
        test_db.remove_namespace(ns_removed,datetime(2015,6,11,19,51,19))
        
        self.assertFalse(ns_removed in test_db.cache.keys())
        
        test_db.update_namespace(ns_to_add)
        self.assertTrue(ns_to_add in test_db.cache.keys())
        
        ns_to_update = 'http://resource.belframework.org/belframework/20150611/namespace/hgnc-human-genes.belns'
        test_db.update_namespace(ns_to_update)
        
        self.assertTrue(ns_to_update in test_db.cache.keys())
        self.assertFalse(ns_to_add in test_db.cache.keys())