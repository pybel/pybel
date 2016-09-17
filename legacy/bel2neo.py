import re,datetime,logging,os,collections,time,copy,sys,ast,django,urllib2,MySQLdb,pybel
from pybel.bel.core import language
from django.core.files.uploadedfile import UploadedFile
from graphManager import Neo4J
from tools.parsers.aetionomy import Parser
from warnings import filterwarnings
 
filterwarnings('ignore', category = MySQLdb.Warning)

class Bel2Neo(Neo4J):
    """Class which handles extract and transform methods for loading BEL documents into Neo4J databases
    
    example
    =======
        To parse a file in Neo4J:
        neo4j on localhost running on port 7474 with no password
            - tip: change in neo4j-server.properties to 'dbms.security.auth_enabled=false' 
            b2n = Bel2Neo() 
        neo4j on 'myserver' running on port 9999 with user 'smartUser' and password 'secretPassword'
            b2n = Bel2Neo('myserver:9999','smartUser','secretPassword')
        load BEL file into Neo4J with
            b2n.parse_File(path_to_File)
    """
    __predefined_translocation_dict = {'sec':{'namespace_from':"MESHCL",
                                                'value_from':"Intracellular Space",
                                                'namespace_to':"MESHCL",
                                                'value_to':"Extracellular Sapce"},
                                              
                                         'surf':{'namespace_from':"MESHCL",
                                                 'value_from':"Intracellular Space",
                                                 'namespace_to':"MESHCL",
                                                 'value_to':"Cell Membrane"}}
    """Dictonary that contains the attributes of predefined translocation-functions."""
    
    __label_dict = {'p':'Protein',
                      'g':'Gene',
                      'm':'MicroRNA',
                      'r':'RNA',
                      'a':'Abundance',
                      'bp':'Biological_process',
                      'path':'Pathology'}
    """Dictionary that translates BEL-functions (bio. entities) to neo4j labels."""
    
    __namespaceAndAnnotations_dict = {
                                        'Namespace':{ 
                                            'NameString':'name',
                                            'Keyword':'keyword',
                                            'DomainString':'domain',
                                            'SpeciesString':'species',
                                            'DescriptionString':'description',
                                            'VersionString':'version',
                                            'CreatedDateTime':'createdDateTime',
                                            'QueryValueURL':'queryValueUrl',
                                            'UsageString':'usageDescription',
                                            'TypeString':'typeClass'
                                            },
                                        'Author':{
                                            'NameString':'authorName',
                                            'CopyrightString': 'authorCopyright',
                                            'ContactInfoString':'authorContactInfo'
                                            },
                                        'Citation':{ 
                                            'NameString':'citationName',
                                            'DescriptionString':'citationDescription',
                                            'PublishedVersionString':'citationPublishedVersion',
                                            'PublishedDate':'citationPublishedDate',
                                            'ReferenceURL':'citationReferenceURL'
                                            },
                                        'Processing':{ 
                                            'CaseSensitiveFlag':'processingCaseSensitiveFlag',
                                            'DelimiterString':'processingDelimiter',
                                            'CacheableFlag':'processingCacheableFlag'
                                            },
                                        'Values':None
                                     }
    __namespaceAndAnnotations_dict['AnnotationDefinition'] = __namespaceAndAnnotations_dict['Namespace']
    """Dictionary that contains the structure of a definition-file for Namespaces or Annotations."""
    
    __complex_statement_map_dict = {(">", ">"):"->",
                                      ("|", "|"):"->",
                                      ("|", ">"):"-|",
                                      (">", "|"):"-|", }
    """Dictionary that is used to translate relations of nested statements."""
    
    # precompiled regular expression: 
    __regex_identify_definition = re.compile('^DEFINE\s*(?P<defined_element>(NAMESPACE|ANNOTATION))\s*(?P<keyName>.+?)\s+AS\s+(?P<definition_type>(URL|LIST))\s+(?P<definition>.+)$')
    """Regular expression that is used to identify definitions of Namespaces and Annotations."""
    
    __regex_activity = re.compile("^\s*(?P<activity>"+
                                  "|".join(language.activities)+
                                  ")\s*\(\s*(?P<activity_parameters>.+)\s*\)\s*$")
    """Regular expression that is used to identify BEL-activities."""
    __regex_function = re.compile("^\s*(?P<term>(?P<function>"+
                                  "|".join(language.functions)+
                                  ")\s*\((?P<function_parameters>.+?)\s*\))\s*$")
    """Regular expression that is used to identify BEL-functions (bio. entities)."""
    # TODO added [^\"] (check if code still runs the same way!!)
    __regex_modification = re.compile("(?P<modification>"+
                                      "|".join(language.modifications)+
                                      ")\s*\(\s*(?P<modification_parameters>.+)\s*\)\s*") 
    """Regular expression that is used to identify modifications."""
    __regex_namespace_value = re.compile('(((?P<namespace>[^\":\(]+)\s*:\s*'+
                                         '(?P<value>((\".+\")|([^\"\),]+))))|(?P<undefined_namespace>\".+\"))')
    """Regular expression that is used to identify namespace:value parameters."""
    __regex_list = re.compile("^\s*(?P<term>(?P<list_function>"+
                              "|".join(language.lists)+
                              ")\s*\((?P<list_parameters>.+)\s*\))\s*$")
    """Regular expression that is used to identify BEL-list-functions."""
    __regex_reaction_parameters = re.compile("^\s*reactants\s*\("+
                                             "(?P<reactant_parameters>.+)\)\s*,\s*products\s*\("+
                                             "(?P<product_parameters>.+)\)\s*$")
    """Regular expression that is used to identify reactants and products of a BEL-reaction-function."""
    __regex_translocation = re.compile("^\s*(?P<translocation_function>("+
                                       "|".join(language.translocations)+
                                       "))\s*\((?P<translocation_parameters>.+)\)\s*$")
    """Regular expression that is used to identify BEL-translocation-functions."""
    __regex_translocation_parameter = re.compile("^(?P<translocated_element>(("+
                                                 "|".join(language.functions+language.lists+language.activities)+
                                                 "))\s*\(\s*(.+)\))\s*,\s*(("+
                                                 "(?P<namespace_from>[^\":\(]+)\s*:\s*"+
                                                 "(?P<value_from>((\".+\")|([^\"\),]+))))|"+
                                                 "(?P<undefined_namespace_from>\".+\"))\s*,\s*(("+
                                                 "(?P<namespace_to>[^\":\(]+)\s*:\s*"+
                                                 "(?P<value_to>((\".+\")|([^\"\),]+))))|"+
                                                 "(?P<undefined_namespace_to>\".+\"))\s*$")
    """Regular expression that is used to identify the parameters of a BEL-translocation-function."""
    __regex_statement = re.compile("^\s*(?P<subject>("+
                                   "|".join(language.activities+language.functions+language.lists+language.translocations)+
                                   ")\s*\(.+\))\s*(?P<relation>"+
                                   "|".join(language.relations)+
                                   ")\s*(?P<object>("+
                                   "|".join(language.activities+language.functions+language.lists+language.translocations)+
                                   ")\s*\(.+\))\s*$")
    """Regular expression that is used to identify BEL-statements."""
    __regex_complex_statement = re.compile("^\s*(?P<subject>("+
                                           "|".join(language.activities+language.functions+
                                            language.lists+
                                            language.translocations)+
                                           ")\s*\(.+\))\s*(?P<relation>"+
                                           "|".join(language.relations)+
                                           ")\s*\(\s*(?P<objectStatement>.+)\s*\)\s*$")
    """Regular expression that is used to identify nested BEL-statements."""
                
    def __init__(self, databaseConnection, defaultTablePrefix):
        """
            :param databaseConnection: Connection to a relational database (DEFAULT: MySQL)
            :type databaseConnection: Connection
            :param defaultTablePrefix: The default prefix for tables that are created by django.
                                       This is usually the name of the app.
            :type defaultTablePrefix: str
        """
        #logfile_folder = os.path.dirname(os.path.realpath(__file__))+os.sep #logfile_folder,
        logfile = "/tmp/logfile_%s.txt" % (str(datetime.datetime.now()))
        logging.basicConfig(filename=logfile, level=logging.ERROR)
        Neo4J.__init__(self)
        self.avoid_zeros_in_neo4j()
        self.mySQLParser = Parser(databaseConnection, defaultTablePrefix)
        self.cursor = databaseConnection.cursor()
        self.undefNS = self.createUndefinedNamespace()
        django.setup()
        
    def avoid_zeros_in_neo4j(self):
        """avoid to have an identifier with 0 in node or edge, add"""
        #if not self._exec('match (n) where id(n)=0 return count(n) as numberOfNodes').one:
        self._graphDB.cypher.execute("create (n:DUMMY)-[r:a]->(n)")
        self._graphDB.cypher.execute("MATCH (n:DUMMY)-[r]-() DETACH DELETE r,n")
            
    def get_graphDB(self):
        return self._graphDB
    
    def print_regular_expressions(self):
        """
            Prints all used regular expressions.
        """
        print "\n== STATEMENT ==\n",
        print self.__regex_statement.pattern
        print "\n== ACTIVITY ==\n"
        print self.__regex_activity.pattern
        print "\n== FUNCTION ==\n"
        print self.__regex_function.pattern
        print "\n== NAMESPACE / VALUE ==\n"
        print self.__regex_namespace_value.pattern
        print "\n== MODIFICATION ==\n"
        print self.__regex_modification.pattern
        print "\n== LIST ==\n"
        print self.__regex_list.pattern
        print "\n== REACTION PARAMETERS ==\n"
        print self.__regex_reaction_parameters.pattern
        print "\n== TRANSLOCATION ==\n"
        print self.__regex_translocation.pattern
        print "\n== TRANSLOCATION PARAMETERS ==\n"
        print self.__regex_translocation_parameter.pattern,"\n"
        
    def parse_Folder(self,path_to_folder,complete_origin=False):
        """
            This method parses all BEL-files in the given folder and sub-folders.
            
            :param path_to_folder: Path to a folder that is containing BEL-Files.
            :type path_to_folder: str
            :param complete_origin: If set to true, proteins will be extended ex. Protein <- translatedTo - RNA <- transcribedTo - Gene
            :type complete_origin: bool
            
        """
        if os.path.isdir(path_to_folder):
            for root, dirs, fileNames in os.walk(path_to_folder):
                for fileName in fileNames:
                    if fileName.endswith('.bel'):
                        filePath = root + os.sep + fileName
                        self.parse_File(filePath,complete_origin)
        else:
            raise Exception("[ERROR] '"+path_to_folder+"' is not a folder.")   
        return True
        
    
    def parse_File(self,path_to_file,context,complete_origin=True,use_multiprocessing=False,print_line_counter=False):
        """
            This method parses the given BEL-file.
            
            :param path_to_file: Path to a BEL-File.
            :type path_to_file: str
            :param complete_origin: If set to true, proteins/RNA will be extended ex. Protein <- translatedTo - RNA <- transcribedTo - Gene
            :type complete_origin: bool
            :param use_multiprocessing: If set to true, multiprocessing will be used for parsing
            :type use_multiprocessing: bool
            
            :return: True
        """
        
         
#         content = [line.strip() for line in file.readlines()]
#         
#         print len(content)
#         
#         startOfStatements = max([i for i, l in enumerate(content) if re.search("(SET\s+DOCUMENT|DEFINE\s+NAMESPACE|DEFINE\s+ANNOTATION)", l, re.I)]) + 1
#         
#         defLines = iter(content[:startOfStatements])
#         statementLines = iter(content[startOfStatements:])
#         
#         
#         [self.create_namespace_or_annotation(path_to_file, line) for line in defLines if re.search('^\s*DEFINE',line)]
#              
#         annotation_informations_dict_default ={'Citation':None,
#                                        'Evidence':None,
#                                        'multiLineEvidence':False,
#                                        'given_annotations':collections.OrderedDict()}
        
        
        fileLable = None
        file = None
         
        if isinstance(path_to_file,UploadedFile):
            file = path_to_file
            fileLabel = file.name
            path_to_file = "UPLOAD/"+fileLabel
        else:
            file = open(path_to_file)
            fileLabel = path_to_file.split(os.sep)[len(path_to_file.split(os.sep))-1].split(".")[0]
        
        if not path_to_file.endswith(".bel"):
            raise Exception("[ERROR] the given file ('"+path_to_file+"') is not a BEL-file!")  
    
        content = [line.strip() for line in file.readlines()]
        startOfStatements = max([i for i, l in enumerate(content) if re.search("(SET\s+DOCUMENT|DEFINE\s+NAMESPACE|DEFINE\s+ANNOTATION)", l, re.I)]) + 1
        
        defLines = iter(content[:startOfStatements])
        statementLines = iter(content[startOfStatements:])
        
        for line in defLines:
            if re.search('^\s*DEFINE',line):
                self.create_namespace_or_annotation(path_to_file, line)

             
        annotation_informations_dict_default ={'Citation':None,
                                       'Evidence':None,
                                       'multiLineEvidence':False,
                                       'given_annotations':collections.OrderedDict()}
        
           
        line_number= startOfStatements
        if print_line_counter:
            start_time = time.time()
            number_of_lines = len(content)#-startOfStatements
            start_line = startOfStatements+1
            logging.info("\nsystem time: ",time.strftime("%H:%M:%S",time.gmtime(time.time())))
        
        formated_end_time = "?"
        remaining_minutes = "?"
        annotation_informations_dict=copy.deepcopy(annotation_informations_dict_default)
        
        logging.info("Parsing Statements.")
        
        for line in statementLines:
            line_number+=1
            if print_line_counter:
#                     line_number+=1
                percent = line_number/(number_of_lines*1.0)
                percent_formated = round(percent*100,1)
                if not (line_number-start_line)%100:
                    now = time.time()
                    time_passed = now-start_time
                    time_needed = time_passed/percent
                    formated_end_time = time.strftime("%H:%M:%S",time.gmtime(now + time_needed))
                    remaining_minutes = int(time_needed-time_passed)/60
                sys.stdout.flush()
                sys.stdout.write('line %s of %s [%s%s](%s%%) need %s min; end at %s\r' % 
                                 (line_number,number_of_lines,
                                  (u"\u2588")*int(percent_formated),
                                  (u"\u259A" if line_number%2 else u"\u259E"),
                                  percent_formated,
                                  remaining_minutes,formated_end_time))
            try:
                line = line.lstrip()
                if line.startswith("SET") or annotation_informations_dict['multiLineEvidence']:
                    # TODO: Reset everything when Citation starts
                    if re.search("^SET\s+Citation\s*=",line):
                        annotation_informations_dict=copy.deepcopy(annotation_informations_dict_default)
                    annotation_informations_dict.update(self.get_annotation(line,annotation_informations_dict))
                
                self.parse_statement(line,annotation_informations_dict,context,complete_origin)
            except:
                logging.exception("-"*60+"\nError in line numer %s\nraised by line:\n%s\n" % (line_number,line))
        return True

    
    def parse_statement(self,statement_string,annotation_informations,context,complete_origin):
        """
            This method identifies the BEL-terms in the given BEL-statement.
            
            :param statement_string: A BEL-statement string. Example: subject-term relation object-term
            :type statement_string: str
            :param annotation_informations: Dictionary that contains the annotation-information for the actual line of BEL-Document
            :type annotation_informations: dict
            :param context: keyword in which context statement is valid
            :type context: str
            :param complete_origin: If set to true, proteins will be extended ex. Protein <- translatedTo - RNA <- transcribedTo - Gene
            :type complete_origin: bool
            
            :return: Dictionary, containing: subject_node, relation, relationType, object_node
            
        """
        
        statement = self.__regex_statement.search(statement_string)
        complexStatement = self.__regex_complex_statement.search(statement_string)   
        
    #     print "Test:",statement_string
    #     if complexStatement:
    #         print "Comples STMNT!",complexStatement.groupdict()
        rel = None
        subject_node = None
        object_node = None
        decoded_relation = None
        try:
            if statement and not complexStatement:
                statement_dict = statement.groupdict()
                
                subject_act = self.__regex_activity.search(statement_dict['subject'])
                subject_tloc = self.__regex_translocation.search(statement_dict['subject'])
                object_act = self.__regex_activity.search(statement_dict['object'])
                object_tloc = self.__regex_translocation.search(statement_dict['object'])
                
                if subject_act:
                    subject_actDict = subject_act.groupdict()
                    subject_node = self.parse_term(term_string = subject_actDict['activity_parameters'].strip(),complete_origin = complete_origin)
               
                elif subject_tloc:
                    subject_tlocDict = subject_tloc.groupdict()
                    subject_tloc_information = self.get_translocation(tloc_function = subject_tlocDict['translocation_function'].strip(), 
                                                                            tloc_parameters = subject_tlocDict['translocation_parameters'].strip())
                    subject_node = subject_tloc_information['translocated_element_node']
                
                else:
                    subject_node = self.parse_term(term_string = statement_dict['subject'].strip(),complete_origin = complete_origin)
                    
                if object_act:
                    object_actDict = object_act.groupdict()
                    object_node = self.parse_term(term_string = object_actDict['activity_parameters'].strip(),complete_origin = complete_origin)
               
                elif object_tloc:
                    object_tlocDict = object_tloc.groupdict()
                    object_tloc_information = self.get_translocation(tloc_function = object_tlocDict['translocation_function'].strip(), 
                                                                           tloc_parameters = object_tlocDict['translocation_parameters'].strip())
                    object_node = object_tloc_information['translocated_element_node']
               
                else:
                    object_node = self.parse_term(term_string = statement_dict['object'].strip(),complete_origin = complete_origin)
                
                if subject_node and object_node:
                    additional_parameters = {'context':context,
                                             'evidence':annotation_informations['Evidence'],
                                             'citation':annotation_informations['Citation'],
                                             'annotations':None,
                                             'subject_activity':None if not subject_act else subject_actDict['activity'],
                                             'subject_translocation':None if not subject_tloc else True, 
                                             'subject_translocation_from_namespace':None if not subject_tloc else subject_tloc_information['namespace_from'],
                                             'subject_translocation_from_value':None if not subject_tloc else subject_tloc_information['value_from'],
    #                                          'subject_translocation_from_no_namespace':None if not subject_tloc else subject_tloc_information['undefined_namespace_from'],
                                             'subject_translocation_to_namespace':None if not subject_tloc else subject_tloc_information['namespace_to'],
                                             'subject_translocation_to_value':None if not subject_tloc else subject_tloc_information['value_to'],
    #                                          'subject_translocation_to_no_namespace':None if not subject_tloc else subject_tloc_information['undefined_namespace_to'],
                                             'object_activity':None if not object_act else object_actDict['activity'],
                                             'object_translocation':None if not object_tloc else True,
                                             'object_translocation_from_namespace':None if not object_tloc else object_tloc_information['namespace_from'],
                                             'object_translocation_from_value':None if not object_tloc else object_tloc_information['value_from'],
    #                                          'object_translocation_from_no_namespace':None if not object_tloc else object_tloc_information['undefined_namespace_from'],
                                             'object_translocation_to_namespace':None if not object_tloc else object_tloc_information['namespace_to'],
                                             'object_translocation_to_value':None if not object_tloc else object_tloc_information['value_to'],
    #                                          'object_translocation_to_no_namespace':None if not object_tloc else object_tloc_information['undefined_namespace_to']
                                            }
                    
                    for given_annotation in annotation_informations['given_annotations']:
                        additional_parameters[given_annotation] = annotation_informations['given_annotations'][given_annotation]
                    decoded_relation = statement_dict['relation'].strip() if statement_dict['relation'].strip() not in language.relations_decode_dict else language.relations_decode_dict[statement_dict['relation'].strip()]
                    rel = self.create_relation(subject_node = subject_node,
                                          object_node = object_node,
                                          relation = decoded_relation,
                                          additional_parameters_dict = additional_parameters) 
                    
                else:
                    fd = open("parsing_errors","a")
                    fd.write("\t"+str(statement_dict))
                    fd.close
    
            elif complexStatement:
                complex_statement_dict = complexStatement.groupdict()
                inner_statement = self.parse_statement(complex_statement_dict['objectStatement'], annotation_informations, context, complete_origin)
                complex_subject_act = self.__regex_activity.search(complex_statement_dict['subject'])
                complex_subject_tloc = self.__regex_translocation.search(complex_statement_dict['subject'])
    
                if complex_subject_act:
                    complex_subject_actDict = complex_subject_act.groupdict()
                    complex_subject_node = self.parse_term(term_string = complex_subject_actDict['activity_parameters'].strip(),complete_origin = complete_origin)
    
                elif complex_subject_tloc:
                    complex_subject_tlocDict = complex_subject_tloc.groupdict()
                    complex_subject_tloc_information = self.get_translocation(tloc_function = complex_subject_tlocDict['translocation_function'].strip(), 
                                                                            tloc_parameters = complex_subject_tlocDict['translocation_parameters'].strip())
                    complex_subject_node = complex_subject_tloc_information['translocated_element_node']
                
                else:
                    complex_subject_node = self.parse_term(term_string = complex_statement_dict['subject'].strip(),complete_origin = complete_origin)
                    
                if complex_subject_node and inner_statement['object_node']:
                    decoded_relation = complex_statement_dict['relation'].strip() if complex_statement_dict['relation'].strip() not in language.relations_decode_dict else language.relations_decode_dict[complex_statement_dict['relation'].strip()]
                    if (decoded_relation[-1],inner_statement['relationType']) in self.__complex_statement_map_dict:
                        resulting_relation = self.__complex_statement_map_dict[(decoded_relation[-1],inner_statement['relationType'])]
                        
                        additional_parameters_dict = {'context':context,
                                                     'evidence':str(annotation_informations['Evidence']),
                                                     'citation':str(annotation_informations['Citation']),
                                                     'subject_activity':False if not subject_act else subject_actDict['activity'],
                                                     'subject_translocation':False if not subject_tloc else True, 
                                                     'subject_translocation_from_namespace':None if not subject_tloc else subject_tloc_information['namespace_from'],
                                                     'subject_translocation_from_value':None if not subject_tloc else subject_tloc_information['value_from'],
            #                                          'subject_translocation_from_no_namespace':None if not subject_tloc else subject_tloc_information['undefined_namespace_from'],
                                                     'subject_translocation_to_namespace':None if not subject_tloc else subject_tloc_information['namespace_to'],
                                                     'subject_translocation_to_value':None if not subject_tloc else subject_tloc_information['value_to']
                                                     }
                                
                        rel = self.create_relation(complex_subject_node, inner_statement['object_node'], resulting_relation, additional_parameters_dict)
                    
    
        except:
            logging.exception("[EXCEPTION] Worker:\n")
    
        return {'subject_node':subject_node,'relation':rel,'relationType':decoded_relation,'object_node':object_node}
    
    def parse_term(self,term_string,complete_origin=False): # TODO: This methode seems to be too long 
        """
            This method identifies the type of the given BEL-term and applies the corresponding regular expressions
            to collect the needed data.
            
            :param term_string: A BEL-term string. Example: p(HGNC:APP)
            :type term_string: str
            :param complete_origin: If set to true, proteins will be extended ex. Protein <- translatedTo - RNA <- transcribedTo - Gene
            :type complete_origin: bool
            
            :return: Py2Neo node-object
            
        """       
        functionWithParametersRegexObj = self.__regex_function.search(term_string)
        listWithParametersRegExObj = self.__regex_list.search(term_string)
        
        node = None
        
        term_dict = {'BEL':None,
                     'function':None,
                     'namespace':None,
                     'value':None,
#                      'valid_NSV':None,
                     'modification':None,
                     'modification_parameters':None}
        
        if functionWithParametersRegexObj:            
            function_dict = functionWithParametersRegexObj.groupdict()
            term_dict['function'] = function_dict['function']
            
            namespaceValue = self.__regex_namespace_value.search(function_dict['function_parameters'])
    
            namespaceValue_dict = {'namespace':'UNDEFINED','value':function_dict['function_parameters']} # CHEBI:"gamma-secretase inhibitor"
            
            if namespaceValue:
                namespaceValue_dict = namespaceValue.groupdict()
                
                if not namespaceValue_dict['namespace']:
                    namespaceValue_dict['namespace'] = "UNDEFINED"
                    namespaceValue_dict['value'] = namespaceValue_dict['undefined_namespace']
                    del(namespaceValue_dict['undefined_namespace'])
            
            term_dict.update(namespaceValue_dict)

            value = self.strip_quotation_marks(term_dict['value']) #if term_dict['value'] else term_dict['undefined_namespace']
            namespace = term_dict['namespace'] #if term_dict['namespace'] else 'UNDEFINED'
            
            term_dict['valid_NSV'],term_dict['value'],term_dict['namespace'] = self.check_NSorA_entry(str(namespace), str(value))
            
            node_term_dict = copy.deepcopy(term_dict)
            node_term_dict['BEL'] = function_dict['function']+"("+str(namespace)+":\""+str(value)+"\")"
            
            node = self.create_node(node_dict = node_term_dict,
                               label = self.__label_dict[node_term_dict['function']],
                               complete_origin = complete_origin)
            
            modification = self.__regex_modification.search(function_dict['function_parameters'])
            if modification:
                modification_dict = self.__regex_modification.search(function_dict['function_parameters']).groupdict()
                term_dict['modification'] = modification_dict['modification']
                term_dict.update(self.get_modification(modification = modification_dict['modification'], 
                                                    modification_parameters = modification_dict['modification_parameters']))
                
    #             term_dict['BEL'] = function_dict['term']
                term_dict['BEL'] = function_dict['function']+"("+str(namespace)+":\""+str(value)+"\","+modification_dict['modification']+"("+modification_dict['modification_parameters']+"))"
                
                mod_node = self.create_node(term_dict,'Modification')
                
                self.create_relation(subject_node = node, 
                                object_node = mod_node, 
                                relation = 'has_modification')
                
                node = mod_node
        
        elif listWithParametersRegExObj:
            list_dict = listWithParametersRegExObj.groupdict()
            term_dict['function'] = list_dict['list_function']
            sub_func = self.__regex_function.search(list_dict['list_parameters'])
            
            if not sub_func:
                if list_dict['list_function'] in ('reaction','rxn'):
                    reaction_parameters_dict = self.__regex_reaction_parameters.search(list_dict['list_parameters']).groupdict()
                    term_dict['BEL'] = list_dict['list_function']+"(reactants("+reaction_parameters_dict['reactant_parameters']+"),products("+reaction_parameters_dict['product_parameters']+"))"
                    node = self.create_node(term_dict, 'Reaction')
                    
                    reactants_list = self.get_list(list_parameters = reaction_parameters_dict['reactant_parameters'])
                    reactant_nodes_list = [self.parse_term(reactant) for reactant in reactants_list]
                    
                    for reactant_node in reactant_nodes_list:
                        self.create_relation(reactant_node, node, 'reactant')
                    
                    products_list = self.get_list(list_parameters = reaction_parameters_dict['product_parameters'])
                    product_nodes_list = [self.parse_term(product) for product in products_list]
                    
                    for product_node in product_nodes_list:
                        self.create_relation(node, product_node, 'product')
                    
                else:
                    term_dict['BEL'] = list_dict['list_function']+"("+list_dict['list_parameters']+")"
                    term_dict.update(self.__regex_namespace_value.search(list_dict['list_parameters']).groupdict())   
                             
            
            if node is None:
                if sub_func and term_dict['function'] in ('complex','composite','list'):
                    sub_func_dict = sub_func.groupdict()
                    term_dict['BEL'] = term_dict['function']+"("+sub_func_dict['function']+"("+sub_func_dict['function_parameters']+"))"
                    term_dict['list'] = "true"
                elif term_dict['function'] in ('complex'):
                    term_dict['BEL'] = list_dict['term']
                node = self.create_node(term_dict, term_dict['function'], complete_origin)
            
            if sub_func:
                participants_list = self.get_list(list_parameters = list_dict['list_parameters'])
                
                participant_nodes_list = [self.parse_term(participant) for participant in participants_list]
                
                for participant_node in participant_nodes_list:
                    self.create_relation(participant_node, node, 'in_list')
            
        else:
            logging.debug("[ERROR] at FUNC / LIST detection [ "+term_string+" ].")
        return node
        
    def get_modification(self,modification,modification_parameters):
        """
            This method is used to identify the parameters of the given modification.
            
            :param modification: BEL representation of the modification (pmod,trunc,sub,fus).
            :type modification: str
            :param modification_parameters: The parameters that are provided to the modification.
            :type modification_parameters: str
            
            :return: Dictionary that contains the identified parameters
        """
        aminoaccid_code_1 = "(?P<aminoacid_Code_1>"+"|".join(language.aminoacids)+")"
        aminoaccid_code_2 = "(?P<aminoacid_Code_2>"+"|".join(language.aminoacids)+")"
        protein_modType = "(?P<p_modType>"+"|".join(language.pmod_parameters_A)+")"
        
        modification_parameters_regexDict = {'trunc': "(?P<position>\d+)",
                                             'sub':   aminoaccid_code_1+"\s*(,\s*(?P<position>\d+)\s*,\s*"+aminoaccid_code_2+")?", #TODO: position and aminoaccid_code_2 are not optional?!
                                             'pmod':  protein_modType+"\s*(\s*,\s*"+aminoaccid_code_1+")?(,\s*(?P<position>\d+))?",
                                             'fus':   self.__regex_namespace_value.pattern+"\s*,*\s(?P<fivePrime>\d+)\s*,\s*(?P<threePrime>\d+)"}
        try:
            return re.search(modification_parameters_regexDict[modification],modification_parameters).groupdict()
        except:
            sys.exit("[ERROR] Modification-search for: "+modification+"("+modification_parameters+")")
        
    def get_translocation(self,tloc_function,tloc_parameters):
        """
            This method identifies the parameters in the given translocation parameters string.
            
            :param tloc_function: The translocation function [tloc,sec,surf].
            :type tloc_function: str
            :param tloc_parameters: The parameters for the given translocation.
            :type tloc_parameters: str
            
            :return: Dictionary containing the translocation informations
            
        """
        translocation_information_dict = {'translocated_element_node':None,
                                          'namespace_from':None,
                                          'value_from':None,
    #                                       'undefined_namespace_from':None,
                                          'namespace_to':None,
                                          'value_to':None,
    #                                       'undefined_namespace_to':None
                                          }
        
        tloc_dict = None
        
        # TODO: Ask Alpha / Raegon for completion of tlocs in BEL-Files!! replace elif tloc_dict
        
        if tloc_function in ('tloc','translocation'):
            tloc = self.__regex_translocation_parameter.search(tloc_parameters)
            tloc_dict = None
            if tloc:
                tloc_dict = tloc.groupdict()
                translocation_information_dict['translocated_element_node'] = self.parse_term(term_string = tloc_dict['translocated_element'])
            else:
                translocation_information_dict['translocated_element_node'] = self.parse_term(tloc_parameters)
                translocation_information_dict['namespace_from'] = 'UNDEFINED'
                translocation_information_dict['value_from'] = 'UNDEFINED'
                translocation_information_dict['namespace_to'] = 'UNDEFINED'
                translocation_information_dict['value_to'] = 'UNDEFINED'
                
    #             translocation_information_dict['undefined_namespace_from'] = "UNDEFINED"
    #             translocation_information_dict['undefined_namespace_to'] = "UNDEFINED"
            
            if tloc_dict and tloc_dict['namespace_from']:
                translocation_information_dict['namespace_from'] = tloc_dict['namespace_from']
                translocation_information_dict['value_from'] = tloc_dict['value_from']
            
            elif tloc_dict:
                translocation_information_dict['namespace_from'] = 'UNDEFINED'
                translocation_information_dict['value_from'] = tloc_dict['undefined_namespace_from']
                
            if tloc_dict and tloc_dict['namespace_to']:
                translocation_information_dict['namespace_to'] = tloc_dict['namespace_to']
                translocation_information_dict['value_to'] = tloc_dict['value_to']
            
            elif tloc_dict:
                translocation_information_dict['namespace_to'] = 'UNDEFINED'
                translocation_information_dict['value_to'] = tloc_dict['undefined_namespace_to']
        
        elif tloc_function in ('sec','surf'):
            translocation_information_dict.update(self.__predefined_translocation_dict[tloc_function])
            translocation_information_dict['translocated_element_node'] = self.parse_term(tloc_parameters)
        
        else:
            logging.error("Translocation-Function is used wrong! [ "+tloc_function+"("+tloc_parameters+")"+" ]")
             
        return translocation_information_dict
    
    def get_list(self,list_parameters):
        """
            This method translates a given list-string to an actual list object.
            
            :param list_parameters: String that represents the parameters of a BEL-list-function
            :type list_parameters: str
            
            :return: List of Strings. The strings represent biological entities (BEL-abundance-functions)
            
        """
        participants = list_parameters.split("),")
        list_participants = [x+")" if not x==participants[len(participants)-1] else x for x in participants]
        return list_participants
    

    def get_citation_dict(self, bel_string):
        """
            parse the citation string and returns a python list
            incides in list  
            0:type,
            1:name,
            2:reference 
            optional 
            3:date
            4:authors
            5:comments
            
            :param bel_string: the citation string
            :type bel_string: str
            
            :return: dict (with 3 to 6 key/value entries) 
        """
        entriesOfCitiationString = re.search('^{\s*(".*")\s*}\s*(#.*)?$', bel_string.strip()).group(1)
        citation_list = re.findall('"([^"]*)"',entriesOfCitiationString)
        if citation_list==2:
            citation_list+=['Not Defined']
        return citation_list

    def get_annotation(self,annotation_string,actual_annotation_info_dict):
        """
            This method identifies the annotations and handle them in an dictionary.
            
            :param annotation_string: The annotation of the actual BEL-Line
            :type annotation_string: str
            :param actual_annotation_info_dict: Is used to handle the annotations (will be updated)
            :type actual_annotation_info_dict: dict
            
            :return: Dictionary containing annotation information
        """
        
        annotation = re.search('^SET\s*(?P<annotation>[^=]+?)\s*=\s*(?P<annotation_content>.+)$',annotation_string)
        un_annotation = re.search('UNSET\s*(?P<annotation>.*)$',annotation_string)
       
        annotation_informations_dict = actual_annotation_info_dict

        if annotation:
            annotation_dict = annotation.groupdict()
            anno_type = annotation_dict['annotation']
    
            if anno_type == "Citation":
                annotation_informations_dict['Citation'] = self.get_citation_dict(annotation_dict['annotation_content'])
            
            if anno_type == "Evidence" or actual_annotation_info_dict['multiLineEvidence']:
                singleLineEvidence = re.search('^"(?P<evidence_text>.+)"$', annotation_dict['annotation_content'])
                multiLineEvidence = re.search('^"(?P<evidence_text>.+)\\\\?$', annotation_dict['annotation_content'])
                
                if singleLineEvidence:
                    evidenceString = singleLineEvidence.groupdict()['evidence_text'].strip()
                    annotation_informations_dict['Evidence'] = evidenceString
                    
                elif multiLineEvidence:
                    annotation_informations_dict['multiLineEvidence'] = True
                    annotation_informations_dict['Evidence'] = multiLineEvidence.groupdict()['evidence_text'].strip().replace("\\","")
            
            elif anno_type not in ('Evidence','Citation'):
                otherAnnotation = annotation_dict['annotation_content'].strip()
                foundAnnotationList = re.search('^{\s*(".*")\s*}$',otherAnnotation)
                if foundAnnotationList:
                    annotation_informations_dict['given_annotations'][anno_type]=list(set(re.findall('"([^"]*)"',foundAnnotationList.group(1))))
                else: 
                    annotation_informations_dict['given_annotations'][anno_type] = [self.strip_quotation_marks(annotation_dict['annotation_content'])]
                 
        elif annotation_informations_dict['multiLineEvidence']:
            annotation_informations_dict.update(actual_annotation_info_dict)
            annotation_informations_dict['Evidence']+= " "+annotation_string.replace("\\","")
            
            if annotation_string.endswith('"'):
                annotation_informations_dict['multiLineEvidence'] = False
                annotation_informations_dict['Evidence'] = annotation_informations_dict['Evidence'][:-1]
               
        elif un_annotation:
            un_anno_dict = un_annotation.groupdict()
            available_annotations = annotation_informations_dict['given_annotations']
           
            if un_anno_dict['annotation']:
                available_annotations.pop(un_anno_dict['annotation'])
            else:
                number_of_keys = len(available_annotations.keys())
                available_annotations.pop(available_annotations.keys()[number_of_keys-1])
                
            annotation_informations_dict['given_annotations'] = available_annotations
        
        return annotation_informations_dict
    
    def create_node(self,node_dict,label=None,complete_origin=False):
        """
            This method executes a cypher-query to create the node described by the node_dict.
            
            :param node_dict: Describes the node that should be created. This is usually the dictionary
                             used in self.parse_term().
            :type node_dict: dict
            :param label: The label that should be attached to the node in the Neo4j-graph.
            :type label: str
            :param complete_origin: If set to true, proteins will be extended ex. Protein <- translatedTo - RNA <- transcribedTo - Gene
            :type complete_origin: bool
            
            :return: Py2Neo node-object.
        """
        
        neo4j_label = ": "+label if label else ""
        neo4j_properties = self.build_cypther_parameters(node_dict)
        cypher_merge = "MERGE (n "+neo4j_label+" "+neo4j_properties+") RETURN n"
        
        node = self._graphDB.cypher.execute_one(cypher_merge)
        
        if complete_origin and label in ('Protein','RNA'): 
            self.create_origin(node_dict, node)  
                
        return node
    
    def create_origin(self,node_dict,node):
        """
            This method creates all origin nodes of a node.
            If the node is a Protein, this method will create an RNA and an Gene Node
            
            :param node_dict: Contains all informations about a node (attributes)
            :type node_dict: dict
            :param node: Entity that will be extended.
            :type node: Py2Neo node object
            
        """
        #TODO: check if this methode is really correct (pmod<-protein<-rna<-gene)
        if node_dict['function'] in ('proteinAbundance','p','rnaAbundance','r'):
            if node_dict['function'] in ('proteinAbundance','p'):
                rna_node_dict = copy.deepcopy(node_dict)
                rna_node_dict['function'] = 'r'
                rna_node_dict['BEL'] = 'r'+"("+node_dict['namespace']+":"+node_dict['value']+")"
                rna_node = self.create_node(rna_node_dict, self.__label_dict['r'],True)
                self.create_relation(rna_node, node, 'translatedTo')
            else:
                gene_node_dict = copy.deepcopy(node_dict)
                gene_node_dict['function'] = 'g'
                gene_node_dict['BEL'] = 'g'+"("+node_dict['namespace']+":"+node_dict['value']+")"
                gene_node = self.create_node(gene_node_dict, self.__label_dict['g'])
                self.create_relation(gene_node, node, 'transcribedTo')
    
    def create_relation(self,subject_node,object_node,relation='UNDEFINED',additional_parameters_dict={}):
        """
            This method creates the relation of two Neo4j-nodes in the Neo4j-graph.
            
            :param subject_node: The context of the relation.
            :type subject_node: Py2Neo node object
            :param object_node: The target of the relation.
            :type object_node: Py2Neo node object
            :param relation: The type of relation between subject_node and object_node.
            :type relation: str
            :param additional_parameters_dict: Contains additional parameters that should be attached to the 
                                               relation.
            :type additional_parameters_dict: dict
                                               
            :return: Py2neo relation-object.
        """
        # strip quotation marks in values of this dict
        additional_parameters_dict = dict([(k,self.strip_quotation_marks(v)) for k,v in additional_parameters_dict.items()])
        rel = self._graphDB.create_unique((subject_node,relation,object_node,additional_parameters_dict))
        
        # because association, positiveCorrelation, negativeCorrelation need both directions add another relation in the opposite direction
        if relation in ("association","positiveCorrelation","negativeCorrelation"):
            altered_parameters_dict = dict([(re.sub('^subject_','object_',k) if k.startswith('subject_') else re.sub('^object_','subject_',k),v) for k,v in additional_parameters_dict.items()])
            self._graphDB.create_unique((object_node,relation,subject_node,altered_parameters_dict))   
        return rel
    

    def insert_namespace_or_annotation_from_url(self, resultDict, values, keyword, attribute, url):
        logging.info('insert definitions from %s' % url)
        if url.startswith("file"):
            filePath = re.search("^file:/// *\[[^;]+;([^]]+)\]$", url).group(1)
            fd = open(filePath)
        else:
            fd = urllib2.urlopen(url)
        lines = re.split("(\r\n|\r|\n)", fd.read())
        for line in lines:
            line = line.strip()
            if line:
                if not re.search('^\s*#.*', line):
                    # If line is not a comment
                    foundKeyword = re.search('^\[([^]]+)\]$', line)
                    if foundKeyword:
                        if foundKeyword.group(1) in self.__namespaceAndAnnotations_dict.keys():
                            keyword = foundKeyword.group(1)
                        else:
                            logging.warning("Unknown keyword %s in %s" % (foundKeyword.group(1), url))
                    elif keyword == "Values":
                        values += [line.rsplit(resultDict['processingDelimiter'], 1)]
                    else:
                        regex = "^(" + "|".join(self.__namespaceAndAnnotations_dict[keyword].keys()) + ") *=(.*)$"
                        foundAttribute = re.search(regex, line)
                        if foundAttribute:
                            attribute = foundAttribute.group(1) # Attribute name in file
                            resultDictKey = self.__namespaceAndAnnotations_dict[keyword][attribute] # column name in database
                            resultDict[resultDictKey] = foundAttribute.group(2)
                        elif keyword and attribute:
                            resultDict[resultDictKey] += line
        
        species = None
        if 'species' in resultDict:
            species = resultDict['species']
            del resultDict['species']
        yesNoDict = {'no':0, 'yes':1}
        for yesNoFiled in 'processingCaseSensitiveFlag', 'processingCacheableFlag':
            if yesNoFiled in resultDict:
                resultDict[yesNoFiled] = yesNoDict[resultDict[yesNoFiled].lower()]
        
        # insert namespace and namespace values
        namespaceAnnotation, notExistsBefore = pybel.models.NamespaceAnnotation.objects.get_or_create(**resultDict)
        if notExistsBefore:
            for entity, encoding in [x for x in values if len(x)==2]: # only excepts if entity and encoding exists
                data = {'namespaceAnnotation_id':namespaceAnnotation.id, 'entry':entity, 'encoding':encoding, 'entryHash':hash(entity.lower())}
                pybel.models.NamespaceAnnotationEntry(**data).save()
            
            if species:
                for taxId in [x.strip() for x in species.split(",")]:
                    taxId = 1 if taxId.lower() == "all" else taxId
                    data = {'namespaceAnnotation_id':namespaceAnnotation.id, 'ncbiTaxonomyID':taxId}
                    pybel.models.NamespaceAnnotationSpecies(**data).save()


    def insert_namespace_or_annotation_from_list(self, path_to_file, defDict, resultDict):
        defList = ast.literal_eval("[" + defDict['definition'].strip()[1:-1] + "]") #TODO: change ast against other solution
        namespaceAnnotation, notExistsBefore = pybel.models.NamespaceAnnotation.objects.get_or_create(**resultDict)
        if notExistsBefore:
            for annotation in defList:
                entry = annotation.strip()
                data = {'namespaceAnnotation_id':namespaceAnnotation.id, 'entry':entry, 'entryHash':hash(entry)}
                pybel.models.NamespaceAnnotationEntry(**data).save()

    def create_namespace_or_annotation(self,path_to_file,definitionLine):
        """
            This method is used to read the definitions for namespaces or annotations and to store
            these definitions into a relational database (DEFAULT: MySQL)
            
            :param path_to_file: Path to the loaded BEL-File.
            :type path_to_file: str
            :param definitionLine: Line from the loaded BEL-File that defines either a namespace or
                                   an annotation.
            :type definitionLine: str
        """
        definition = self.__regex_identify_definition.search(definitionLine)
        if definition:
            try:
                defDict = definition.groupdict()
                resultDict = {'urlOrPath':defDict['definition'].strip('"'), 
                              'shortName':defDict['keyName'], 
                              'typeOfDoc':defDict['defined_element'][0]}
                values = [] 
                keyword = None
                attribute = None
                url = resultDict['urlOrPath']
                     
                if defDict['definition_type'] == "URL" and not pybel.models.NamespaceAnnotation.objects.filter(urlOrPath=url).first():
                    self.insert_namespace_or_annotation_from_url(resultDict, values, keyword, attribute, url) 
                         
                elif defDict['definition_type'] == "LIST":
                    resultDict['urlOrPath'] = path_to_file + ":" + defDict['keyName']
                    if not pybel.models.NamespaceAnnotation.objects.filter(urlOrPath=resultDict['urlOrPath']).first():
                        self.insert_namespace_or_annotation_from_list(path_to_file, defDict, resultDict)
            except:
                logging.exception("problems to load namespace from "+path_to_file+str(resultDict))                
     
    def check_NSorA_entry(self,namespaceOrAnnotationKey,entry):
        """
            This method checks if the combination of namespace key and value is valid.
             
            :param namespaceOrAnnotationKey: The keyword that is used to represent the namespace or annotation in the loaded BEL-File. (Example: HGNC)
            :type namespaceOrAnnotationKey: str
            :param entry: Value that is used in the namespace or annotation. (Example: APP)
            :type entry: str
             
            :return: ([+|-),entry)
                     Returns a - if the entry is not defined in the namespace or annotation.
                     Returns a + if the entry is defined in the namespace or annotaiton.
                     Returns a corrected entry
        """
        is_valid = '-'
        # TODO: Check is not OK, assume a hash problem 
        foundEntry =pybel.models.NamespaceAnnotationEntry.objects.filter(namespaceAnnotation__shortName=namespaceOrAnnotationKey,namespaceAnnotation__isValid=True,entryHash=hash(entry.lower())).first()
        if foundEntry:
            is_valid = '+'
            entry = foundEntry.entry
        else:
            foundInAnotherNS = pybel.models.NamespaceAnnotationEntry.objects.filter(namespaceAnnotation__isValid=True,entryHash=hash(entry.lower()))
            if len(foundInAnotherNS)==1:
                entry = foundInAnotherNS[0].entry
                namespaceOrAnnotationKey = foundInAnotherNS[0].namespaceAnnotation.shortName
        return is_valid, entry, namespaceOrAnnotationKey
     
    def insertToUndefinedNamespace(self, value):
        """
            This method inserts a value like a("Amyloid beta-peptides") to the relational database like: a(UNDEFINED:"Amyloid beta-peptides").
             
            :param value: The value that has no namespace, this would be "Amyloid beta-peptides" in the previous example.
            :type value: str
            
            :return: ID of the mapping of namespace "UNDEFINED" to the value.
        """
        undefNSV_id = self.mySQLParser.insertData('namespaceannotationentry', {'namespaceAnnotation_id':self.undefNS, 'entry':MySQLdb.escape_string(value), 'encoding':None}, unique=True)
         
        return undefNSV_id
     
    def createUndefinedNamespace(self):
        """
            This method creates a default namespace for entries like: a("Amyloid beta-peptides").
             
            :return: The id of the default namespace in the relational database.
        """
        defaultNSDict = {'urlOrPath':'http://www.UndefinedNamespace.de', 'shortName':'UNDEFINED', 'typeOfDoc':'N', 'keyword':'UNDEFINED'}
        defaultNSID = self.mySQLParser.insertData('namespaceannotation', defaultNSDict, unique4ColumnList=('urlOrPath'), unique=True)
         
        return defaultNSID
