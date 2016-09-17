import py2neo, re, pybel,django
import networkx as nx

def getNodesAndEdgesByNodeProperties(nodeProperties,direction):
    """
    returns dictionary of statement
    :param nodeProperties: all properties of a node in Neo4J
    :type  nodeProperties: dict
    """
    return Neo4J().getNodesAndEdgesByNodeProperties(nodeProperties,direction)

def getNodesAndEdgesByEdgeProperties(edgePropList,nodeIds=[],context=None):
    return Neo4J().getNodesAndEdgesByEdgeProperties(edgePropList,nodeIds,context)
    
def getNodesAndEdgesByEdgeProperty(key, value):
    return getNodesAndEdgesByEdgeProperties([(key, value)])

def getNodesAndEdgesByEdgePropertyId(propertyId):
    property = pybel.models.Property.objects.get(pk=propertyId)
    return getNodesAndEdgesByEdgeProperties([(property.key, property.value)])

def getNodesAndEdgesByEdgePropertyIds(propertyIds,nodeIds=[],context=None):
    propertyList = [(x.key, x.value) for x in pybel.models.Property.objects.filter(id__in=propertyIds)]
    return getNodesAndEdgesByEdgeProperties(propertyList,nodeIds,context)

def getShortestPathsByNamespaceValue(namespaceFrom,valueFrom,namespaceTo,valueTo):
    return Neo4J().getShortestPathsByNamespaceValue(namespaceFrom,valueFrom,namespaceTo,valueTo)

def getBelStatementByEdgeId(edgeId):
    return Neo4J().getBelStatementByEdgeId(edgeId)

def getNetworkxGraph():
    return Neo4J().getNetworkxGraph()

def getAllContexts():
    return list(pybel.models.Context.objects.exclude(shortName__isnull=True).values())
    
def getNeo4jGraph():
    return Neo4J().getGraphDB()

def getNeo4jExec():
    return Neo4J().getExec()

class Neo4J:
    def __init__(self):
        self._graphDB = py2neo.Graph("http://%s/db/data" % django.conf.settings.NEO4J_CONN_STR)
        self._exec = self._graphDB.cypher.execute
    
    def getGraphDB(self):
        return self._graphDB
    
    def getExec(self):
        return self._exec
    
    def truncateAll(self):
        self._exec("MATCH (n) DETACH DELETE n")
    
    def getNodesAndEdgesByNodeProperties(self,nodeProperties,direction=None):
        if direction:
            cypherDorection = {'to':"(m)-[r]->(n)",'from':"(n)-[r]->(m)"}
            where = ' and '.join(['n.'+k+'="'+v+'"' for k,v in nodeProperties.items()])
            cypherQuery = "match %s where %s return id(n) as nid, n, type(r) as rtype, id(r) as rid,r,id(m) as mid,m,r.context as context" % (cypherDorection[direction],where)
#             print cypherQuery 
            results = self._exec(cypherQuery)
            
            return self._getNodesAndEdgesDictFromNeo(results)
            
        else:
            return {'to':self.getNodesAndEdgesByNodeProperties(nodeProperties,direction='to'),'from':self.getNodesAndEdgesByNodeProperties(nodeProperties,direction='from')}
        
    def numberOfNodes(self):
        return self._exec("match (n) return count(distinct n) as numberOfNodes")[0].numberOfNodes

    def _getNodesAndEdgesDictFromNeo(self, py2neo_resultSet):
        """
            This method builds a dictionary for nodes and edges.
            
            :note: The used cypher query must return the following information:
                return id(n) as nid, n, type(r) as rtype, id(r) as rid,r,id(m) as mid,m,r.context as context
        """
        
        nodes = set()
        edges = []
        
        for nid, n, rtype, rid, r, mid, m, context in py2neo_resultSet:
            nodes |= set([tuple(n.properties.items()) + (('id', nid),), tuple(m.properties.items()) + (('id', mid),)])
            edges += [dict([('id', rid), ('label', rtype), ('from', nid), ('to', mid), ('context',context)])]
        nodes = [dict(x) for x in nodes]            
            
        return {'nodes':nodes, 'edges':edges}

    def build_cypther_parameters(self, param_dict):
        """
            Translates a given dictionary into a Cypher-query properties set as string.
            
            :param param_dict: Contains parameters that should be contained in the query.
            :type param_dict: dict
            
            :return: String that represents the Cdef getNodesAndEdgesByEdgeProp(self,key,value):ypher statement for the given parameters.
        """
        return "{" + ",".join([k + ":'" + self.strip_quotation_marks(v).replace("'", "\\'") + "'" for k, v in param_dict.items() if v]) + "}"
    
    def strip_quotation_marks(self, term):
        if type(term) in (str, unicode):
            found = re.search('^\s*"\s*(.*)\s*"\s*$', term)
            if found:
                term = found.group(1)
        return term
    
    def delete_all(self):
        """
            Deletes all nodes and edges
            :return: number of nodes
        """
        self._graphDB.delete_all()
        
    def getNodesAndEdgesByEdgeProperties(self, edgePropList,nodeIds=[],context=None):
        """
        return a py2neo object result
        """
        nodeIdsString = str([int(x) for x in nodeIds if re.search('^\d+$',x)])
        whereProps = " or ".join(['"' + x[1] + '" in r.' + x[0] for x in edgePropList])
        whereNodeIds = ("and (id(n) in %s or id(m) in %s)" % (nodeIdsString,nodeIdsString)) if nodeIds else ''
        whereContext = "{context:'"+context+"'}" if context else ''
        cypherString = 'match (n)-[r %s]->(m) where (%s) %s return id(n) as nid, n,type(r) as rtype,id(r) as rid,r,id(m) as mid,m, r.context as context' % (whereContext,whereProps,whereNodeIds)
        print nodeIds,cypherString
        resultList = self._exec(cypherString)           
        return self._getNodesAndEdgesDictFromNeo(resultList)
    
    def getShortestPathsByNamespaceValue(self,namespaceFrom,valueFrom,namespaceTo,valueTo):
        where = "n.namespace='%s' and n.value='%s' and m.namespace='%s' and m.value='%s'" % (namespaceFrom,valueFrom,namespaceTo,valueTo)
        cypherString = 'MATCH path = shortestPath((n)-[r*..3]->(m)) where %s return path' % where
        return [{'nodes':self._py2neoNodesToPythonObjects(x.path.nodes),'edges':self._py2neoEdgesToPythonObjects(x.path.rels)} for x in self._exec(cypherString)]
    
    def _py2neoNodesToPythonObjects(self,listOfNodes):
        return [{'id':int(node.ref.split("/")[1]),'properties':node.properties} for node in listOfNodes]             

    def _py2neoEdgesToPythonObjects(self,listOfEdges):
        return [{'id':int(edge.ref.split("/")[1]),'label':edge.type,'context':edge.properties["context"],'from':edge.start_node.ref.split("/")[1],'to':edge.end_node.ref.split("/")[1]} for edge in listOfEdges] #,'properties':edge.properties.filter()

    def getBelStatementByEdgeId(self, edgeId):
        cypherString = 'MATCH (n)-[r]->(m) where id(r)=%s return n.BEL,r,m.BEL limit 1' % edgeId
        nBel, r, mBel = self._exec(cypherString)[0]
        if r['subject_translocation'] == True:
            nBel = "translocation("+nBel + "," + r['subject_translocation_from_namespace'] + ':"' + r['subject_translocation_from_value'] + \
                "," + r['subject_translocation_to_namespace'] + ':"' + r['subject_translocation_to_value'] + '")'
        if r['object_translocation'] == True:
            mBel = "translocation("+mBel + "," + r['object_translocation_from_namespace'] + '"' + r['object_translocation_from_value'] + \
                "," + r['object_translocation_to_namespace'] + ':"' + r['object_translocation_to_value'] + '")'
        sA, oA = [((x, '(', ')') if x else ('', '', '')) for x in [r['subject_activity'], r['object_activity']]]
        statement = sA[0] + sA[1] + nBel + sA[2] + ' ' + r.type + ' ' + oA[0] + oA[1] + mBel + oA[2] 
        return statement 
    

    def getNetworkxGraph(self):
        """Returns a NetworkX di-graph instance
        """
        excluded_values = ['Alzheimer',"Alzheimer's disease",'Parkinson',"Parkinson Disease",'Alzheimer Disease',"Early_Onset_Alzheimer_s_Disease","Early_onset_Alzheimer_s_Disease",'Late_Onset_Alzheimer_s_Disease','Late_onset_Alzheimer_s_Disease']
        excluded_namespaces = ['MESHD','PDO','ADO']
        excluded_functions =['path','bp']
        
        if nx is None:
            raise ImportError("Try installing NetworkX first.")
        graph = nx.MultiDiGraph()
        for r in self._exec("match (n) return id(n) as n_id,n"):
            node_props = dict(r.n.properties)
            node_props.update({'labels':list(r.n.labels)})
            graph.add_node(r.n_id,None,**node_props)
        for r in self._exec("match ()-[r]->() return id(r) as r_id,r"):
            start = r.r.start_node.properties
            end = r.r.end_node.properties
            if start.has_key('value') and (start['value'] in excluded_values or start['namespace'] in excluded_namespaces or start['function'] in excluded_functions):
                weight = 10
            elif end.has_key('value') and (end['function'] in excluded_functions or end['value'] in excluded_values or end['namespace'] in excluded_namespaces):
                weight = 10
            else:
                weight=1
            edge_props = dict(r.r.properties)
            edge_props.pop('citation',None)
            edge_props.update({'type':r.r.type,'weight':weight})
            graph.add_edge(int(r.r.start_node.ref.split("/")[1]),int(r.r.end_node.ref.split("/")[1]),None,**edge_props)
        return graph