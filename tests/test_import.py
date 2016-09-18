import unittest

import networkx as nx

import pybel


class TestImport(unittest.TestCase):
    def setUp(self):
        self.graph = nx.MultiDiGraph()

        self.graph.add_node('TestValue1', namespace='TestNS1')
        self.graph.add_node('TestValue2', namespace='TestNS1')
        self.graph.add_node('TestValue3', namespace='TestNS1')
        self.graph.add_node('TestValue4', namespace='TestNS1')
        self.graph.add_node('TestValue5', namespace='TestNS1')

        self.graph.add_edge('TestValue1', 'TestValue2', attr_dict={
            'Citation': ("Pubmed", "That one article from last week", "123455"),
            'Evidence': "Evidence 1 w extra notes",
            'TESTAN1': 'TestAnnot1',
            'relation': 'increases'
        })
        self.graph.add_edge('TestValue2', 'TestValue3', attr_dict={
            'Citation': ("Pubmed", "That one article from last week", "123455"),
            'Evidence': "Evidence 1 w extra notes",
            'TESTAN1': 'TestAnnot1',
            'relation': 'decreases',
            'TESTAN2': 'B'
        })
        self.graph.add_edge('TestValue2', 'TestValue4', attr_dict={
            'Citation': ("Pubmed", "That one article from last week", "123455"),
            'Evidence': "Evidence 1 w extra notes",
            'TESTAN1': 'TestAnnot1',
            'relation': 'directlyDecreases',
            'TESTAN2': 'B'
        })
        self.graph.add_edge('TestValue4', 'TestValue5', attr_dict={
            'Citation': ("Pubmed", "That other article from last week", "123456"),
            'Evidence': "Evidence 3",
            'TESTAN1': 'TestAnnot2',
            'relation': 'association'
        })

    def test(self):
        result = pybel.from_url('http://localhost:8000/test_bel_1.bel')
        self.assertSetEqual(set(self.graph.nodes()), set(result.nodes()))
