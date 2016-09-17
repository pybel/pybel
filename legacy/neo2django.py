import django,hgnc,sys,logging,datetime,re,cPickle, graphManager,pybel
from tools.databases import mysql
from graphManager import Neo4J
from pybel.bel.extentions.pubmed import get_pubmedInfos_by_pmidList
from pybel.models import NetworkxGraph, NamespaceAnnotation, Function, Edge, Property
from django.db import IntegrityError
from django.forms.models import model_to_dict
from pybel.bel.core.language import activities_dict

class Neo2Django:
    """Extracts all information out of Neo4J in Django models (MySQL)"""
    tablePrefix="pybel_"

    def __init__(self):
        self.c = django.db.connection.cursor()  # @UndefinedVariable
        logfile = "logfile_%s.txt" % str(datetime.datetime.now())
        logging.basicConfig(filename=logfile, level=logging.ERROR)
        neo=Neo4J()
        self._graphDB = neo.getGraphDB()
        self._exec = neo.getExec()


    def transferDataFromNeo4J2Django(self):
        logging.info("insert activities from pybel.bel.core.language.acticities")
        self.__insertDefaultActivities()
        logging.info("save nodes")
        self.__save_nodes()
        logging.info("save edges")
        self.__save_edges()
        logging.info("correct citations")
        self.__correct_citations()
        logging.info("safe networkx object in database")
        self.__neo2networkx()

    def __insertDefaultActivities(self):
        for longName,shortName in activities_dict.items():
            pybel.models.Activity.objects.get_or_create(shortName=shortName,longName=longName)

    def __neo2networkx(self):
        defaultNetwork = NetworkxGraph.objects.filter(name='default').first()
        if defaultNetwork:
            defaultNetwork.delete()
        networkxGraph=cPickle.dumps(graphManager.getNetworkxGraph())
        NetworkxGraph(name='default',networkxGraph=networkxGraph).save()

    def _truncate_tables(self):
        """truncates all tables except namespace/annotation realted
        :return: void"""
        [self.c.execute('truncate '+self.tablePrefix+x) for x in ('author','edge_citations','citation','edge','edge_properties','function','node','property','funcnsvalue','label','modification','node_labels')]

    def getAllNodeIds(self):
        """Get all node IDs from django models"""
        return [x.id for x in pybel.models.Node.objects.all().only('id')]

    def __save_nodes(self):
        """store the neo4j graph nodes in Django(mysql)"""
        nodeIDsInDjango = self.getAllNodeIds()
        r = self._exec("match (n) return n,id(n),labels(n)")
        for neo_node,_id,labels in r:
            if _id not in nodeIDsInDjango:
                #print 'node_id not in django',_id
                p = neo_node.properties
                v = p['value']
                dj_hgnc = None
                if p['namespace'] and p['namespace'].lower()=='hgnc':
                    hgncs_found = hgnc.models.Hgnc.objects.filter(symbol=v)
                    if hgncs_found:
                        dj_hgnc = hgncs_found[0]
                try:
                    namespaceAnnotation=None
                    if p['namespace']:
                        namespaceAnnotation = NamespaceAnnotation.objects.filter(keyword=p['namespace'],isValid=True).first()
                    function = Function.objects.get_or_create(name=p['function'])[0]
                    hashId=hash((function.id,(namespaceAnnotation.id if namespaceAnnotation else None),v,dj_hgnc,p['valid_NSV']))
                    dj_funcNsValue = pybel.models.FuncNsValue.objects.get_or_create(function=function,namespace=namespaceAnnotation,value=v,hgnc=dj_hgnc,hashId=hashId,validNSV=p['valid_NSV'])[0]  # @UndefinedVariable
                except IntegrityError:
                    print "Problems to execute following SQL:"
                    print '\n\nfunction:',p['function'],'\nnamespace:',p['namespace'],'\nvalue:',v,'\nhgnc:',dj_hgnc
                    raise
                except:
                    print "Unexpected error:", sys.exc_info()[0]
                    raise
                dj_modification=None
                if 'Modification' in labels:
                    modificationParams = ('aminoacid_Code_1','aminoacid_Code_2','p_modType','position','modification','fivePrime','threePrime')
                    params4Modification = dict([(mysql.get_standard_column_name(k),v) for k,v in p.items() if k in modificationParams])
                    params4Modification.update(dict([(mysql.get_standard_column_name(x),None) for x in modificationParams if x not in p]))
                    dj_modification = pybel.models.Modification.objects.get_or_create(**params4Modification)[0]  # @UndefinedVariable
                dj_node = pybel.models.Node(id=_id,funcNsValue=dj_funcNsValue, modification=dj_modification)
                for label in labels:
                    labelEntry = pybel.models.Label.objects.get_or_create(name=label.strip())[0]# @UndefinedVariable
                    labelEntry.save()
                    dj_node.labels.add(labelEntry)
                dj_node.save()
        del(r)


    def __correct_citations(self):
        """Corrects and extend PubMed information. Because often PMID is stored in comments first try to get PMID from reference and then from comment"""
        self.c.execute("update "+self.tablePrefix+"citation set reference=trim(reference),comment=trim(comment),citationType=trim(citationType)")
        citations = pybel.models.Citation.objects.filter(reference__iregex='^[0-9]+$',citationType__iexact='PubMed',journal__isnull=True)
        pmids = [x.reference for x in citations]
        pmids_with_PubMedInfos = get_pubmedInfos_by_pmidList(pmids)
        for pmid,p in pmids_with_PubMedInfos.items():
            cits = pybel.models.Citation.objects.filter(reference=pmid)
            cits.update(
                authors=p['authors'],
                title=p['title'],
                pubdate=p['pubdate'],
                lastauthor=p['lastauthor'],
                journal=p['journal'],
                volume=p['volume'],
                issue=p['issue'],
                pages=p['pages'],
                firstauthor=p['firstauthor'],
                pmcId=p['pmcId'])
            #print cits
            #for cit in cits:
            #    for edgeId in [x.id for x in cit.edge_set.all()]:
            #        self._exec("match ()-[r]->() where id(r)={edgeId} set r.citation=['PubMed',{journal},{pmid}]", edgeId=edgeId,journal=p['journal'],pmid=pmid)


    def __saveProperties(self, edge_py2neo, edge_django):
        for k, v in edge_py2neo.properties.items():
            if (type(v) == bool or v) and k not in ['context', 'citation', 'object_activity', 'subject_activity']:
                if type(v) in (unicode, str, int, bool):
                    prop = Property.objects.get_or_create(key=k, value=v, valueHash=hash(v))[0]
                    edge_django.properties.add(prop)
                elif type(v) == list:
                    for entry_in_list in v:
                        prop = Property.objects.get_or_create( # @UndefinedVariable
                            key=k, value=entry_in_list, valueHash=hash(entry_in_list))[0]
                        edge_django.properties.add(prop)

    def __getActivity(self,edge_py2neo,subjectOrObject):
        activity_django = None
        activity = edge_py2neo.properties.pop(subjectOrObject+'_activity',None)
        if activity and activity.strip():
            if activity in activities_dict:
                activity_django = pybel.models.Activity.objects.get(longName=activity)
            else:
                activity_django = pybel.models.Activity.objects.get(shortName=activity)
        return activity_django


    def __saveCitation(self, edge_py2neo):
        citationInNeo = edge_py2neo.properties.pop('citation', None)
        citation = None
        try:

            if citationInNeo:
                if len(citationInNeo) >= 6 and re.search('^\s*pubmed\s*$', citationInNeo[0], re.I) and re.search('^\d+$', citationInNeo[5]):
                    citationInNeo[2] = citationInNeo[5]
                citationType, name, reference = citationInNeo[:3]
                if re.search('^\s*pubmed\s*$', citationType, re.I):
                    citation = pybel.models.Citation.objects.filter(citationType=citationType, reference=reference).first()
                else:
                    citation = pybel.models.Citation.objects.filter(citationType=citationType, name=name, reference=reference).first()
                if not citation:
                    citation = pybel.models.Citation(
                        citationType=citationInNeo[0],
                        name=citationInNeo[1],
                        reference=citationInNeo[2],
                        date=citationInNeo[3] if len(citationInNeo) >= 4 else None,
                        authors=citationInNeo[4] if len(citationInNeo) >= 5 else None,
                        comment=citationInNeo[5] if len(citationInNeo) >= 6 else None)
                    citation.save()
        except:
            logging.exception('Error: Citation > '+str(citationInNeo))
        return citation

    def __save_edges(self):
        """save edges"""
        edgeIDsInDjango = Edge.objects.values_list('id',flat=True)
        r2 = self._exec("match (n)-[r]->(m) return r,id(n) as fromId,id(r) as r_id,id(m) as toId")
        for e in r2:
            if e.r_id not in edgeIDsInDjango and e.r_id!=0:
                context = e.r.properties.pop('context', None)
                if context is not None:
                    context = pybel.models.Context.objects.get_or_create(shortName=context)[0]
                citation = self.__saveCitation(edge_py2neo=e.r)
                values = {
                          'id':e.r_id,
                          'fromNode_id':e.fromId,
                          'toNode_id':e.toId,
                          'relation':e.r.type,
                          'weight':e.r.properties['weight'],
                          'context':context,
                          'citation':citation,
                          'subjectActivity':self.__getActivity(e.r, 'subject'),
                          'objectActivity':self.__getActivity(e.r, 'object')}
                edge = Edge(**values)
                edge.save()
                self.__saveProperties(edge_py2neo=e.r, edge_django=edge)
        del(r2)
