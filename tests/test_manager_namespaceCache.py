import unittest
import os

dir_path = os.path.dirname(os.path.realpath(__file__))

from pybel.manager.namespacecache import NamespaceCache
from datetime import datetime

class TestNsCache(unittest.TestCase):

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
    
    def test_update(self):
        
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