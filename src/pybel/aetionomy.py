import MySQLdb, _mysql_exceptions, lxml, re, urllib, os, zipfile, gzip, tarfile, django
from tools.databases import mysql


class Parser:
    '''
    classdocs
    '''
    dataFolder = None
    def __init__(self,databaseConnection,defaultTablePrefix):
        """
        @param databaseConnection[MySQLdb.connections.Connection]: MySQL database connection 
        """
        django.setup()
        self.connection = databaseConnection
        self.cursor = self.connection.cursor()
        self.dbHost = mysql.get_hostname(self.cursor)
        self.dbUser = mysql.get_user(self.cursor)
        self.dbName = mysql.get_database_name(self.cursor)
        self.defaultTablePrefix = defaultTablePrefix if defaultTablePrefix.endswith('_') else defaultTablePrefix+"_"

    def setNullWhereEmpty(self):
        for table in self.getTableNames():
            mysql.set_null_where_empty(self.cursor, table)

    def get_taxonomyIdByOrganismName(self,name):
        """get a dictiontay of organism names (key) and  NCBI taxonomy identifier(s)(value) by organism name(s). 
        First try to find by scientific name, next by all others.
        If no taxIds is found the method try to split the name by ( and other |, and | and |,) and 
        Warning if more than one tax-ID is connected to this name
        TODO: there could be more than one scientific name, take the min(taxIdentifier) 
        with the assumption that this is higher in the hierarchy
        returns 
        1. {NCBI taxonomy scientific name:NCBI taxonomy id} 
            (if one organism is mentioned and found in ncbi taxonomy) or 
        2. {original name:None,NCBI taxonomy scientific name:NCBI taxonomy id,...} 
            (if several organisms mentioned and found in ncbi taxonomy) or 
        @param name: (string) any organism name(s)
        @return: (dictionary)    
        """
        sql_findOrganismByScientificName="Select taxIdentifier from ncbiTaxonomy_name where (className='scientific name' or className='genbank common name') and name like '%s' order by taxIdentifier"
        namesTaxIdsDict = {name:None}
        if name and name.strip():
            if not hasattr(self, 'ncbiTaxonomyNameTableExists'): 
                if 'ncbiTaxonomy_name' in mysql.get_table_names(self.cursor):
                    self.ncbiTaxonomyNameTableExists=True
                else:
                    self.ncbiTaxonomyNameTableExists=False
            if self.ncbiTaxonomyNameTableExists:
                name = MySQLdb.escape_string(name.strip().encode('utf8'))
                found_scientific_name = self.cursor.execute(sql_findOrganismByScientificName % name)
                if found_scientific_name:
                    if found_scientific_name>1:
                        print "WARNING: found more than one taxId for the scientific organism name",name
                    namesTaxIdsDict[name]=self.cursor.fetchone()[0]
                elif found_scientific_name==0: # try to split the name by (',','and','' )
                    splittedNames = [x.strip() for x in re.split("( and other |, and | and |,)",name)]
                    if len(splittedNames)>1:
                        for splittedName in splittedNames:
                            if self.cursor.execute(sql_findOrganismByScientificName % splittedName):
                                namesTaxIdsDict[splittedName]=self.cursor.fetchone()[0]
            else:
                raise NameError('ncbiTaxonomy_name table not exists. Execute ncbiTaxonomy.scripts.parser')
        return namesTaxIdsDict

    def set_dataFolder(self,folder):
        self.dataFolder = folder if folder.endswith(os.sep) else folder.strip()+os.sep
        return self.dataFolder 

    def download_and_extract(self,url,destinationFolder="",fileName=None,**kargs):
        """download url to dataFolder if is set else to destination. If file is zipped or gzipped this method extract the file
        returns the list of file names of the download (and extracted file). if file will be extracted only extracted files are in the list
        @param url: URL (string) to a file to download  
        @param destinationFolder: path to the folder where to download the url
        @return: list of file names
        """
        destinationFolder = self.dataFolder if not destinationFolder else destinationFolder
        destinationFolder = destinationFolder if destinationFolder.endswith(os.sep) else destinationFolder+os.sep
        if not fileName:
            fileName = [x.strip() for x in url.split("/") if x.strip()][-1]
        filePath = destinationFolder+fileName 
        if not os.path.isdir(destinationFolder):
            os.makedirs(destinationFolder)
        if not os.path.isfile(filePath) or ('downloadAnyway' in kargs and kargs['downloadAnyway']==True):
            print "download",filePath
            urllib.urlretrieve(url,filePath)
        else:
            print "download file already exists"
        if 'unzip' in kargs and kargs['unzip']==False:
            fileList=[fileName]
            print "file will be not extracted"
        else:
            if zipfile.is_zipfile(filePath):
                print "unzip",filePath
                myzipFile = zipfile.ZipFile(filePath)
                fileList = [destinationFolder+str(x) for x in myzipFile.infolist()]
                myzipFile.extractall(destinationFolder)
            elif tarfile.is_tarfile(filePath): # first check if it tar.gz and than gz
                print "untar and gunzip"
                tar = tarfile.open(filePath)
                fileList = [x.name for x in tar.getmembers()]
                tar.extractall(destinationFolder)
                tar.close()
            elif filePath.endswith(".gz"):
                print "gunzip"
                newFileName = fileName[:-3] 
                gunzippedFile = open(destinationFolder+newFileName,"w")
                gzippedFile = gzip.open(filePath, 'r')
                gunzippedFile.write(gzippedFile.read())
                gzippedFile.close()
                gunzippedFile.close()
                fileList=[newFileName]
            else:
                fileList=[fileName]
        return fileList

    def optimize_data_types(self):
        """ALERT: Could be very dangerous because datatype will be changed: execute standard optimization to table"""
        tables = self.getTableNames()
        if len(tables)>0: # to 
            mysql.optimize_data_types(self.cursor, tables)
        else:
            raise NameError('No tables to optimize with prefix '+self.defaultTablePrefix)

    def filterColValDict4ColumnNames(self,table,colValDict):
        """filters the colValDict for all keys which have also a counterpart in the table. all other keys will be deleted"""
        columns = mysql.get_column_names(self.cursor, self.defaultTablePrefix+table)
        if 'id' in columns:
            del columns[columns.index('id')]
        for key in set(colValDict.keys())-set(columns):
            del colValDict[key]
        return colValDict
        

    def escape4Sql(self,value):
        """surround value with single quotes and prepare for SQL statement
        @param value[None,int,long or string]: value to be changed
        @return: value with surrounding single quotes
        """
        if value == None:
            value = "NULL"
        elif type(value) in [int, long, float]:
            value = str(value)
        else:
            try:
                value = "'" + MySQLdb.escape_string(value) + "'"
            except UnicodeEncodeError:
                value = "'" + MySQLdb.escape_string(value.encode('utf-8')) + "'"
        return value

    def insertDataIfNull(self,table, colValDict, unique=False, unique4ColumnList=None):
        """Check if something to store and call the insertData method otherwise return a None"""
        if set(colValDict.values()) == set([None]):
            return None
        return self.insertData(table, colValDict, unique, unique4ColumnList, insertIgnore=False)

    def insertIgnoreData(self,table, colValDict, unique=False, unique4ColumnList=None):
        """uses the 'insert ignore' statement form MySQL in the insertData method"""
        self.insertData(table, colValDict, unique, unique4ColumnList, insertIgnore=True)

    def insertData(self,table, colValDict, unique=False, unique4ColumnList=None, insertIgnore=False,insertDelayed=False,insertUpdate=False,filter4ColumnNames=False,printSql=False):
        """generic method to insert data into the database
        @param table[string]: table name
        @param colValDict[dictionary]: dictionary of column names (dict keys) and values (dict values) example {'column1':"value1"}
        @param unique[boolean]: set this TRUE if all these values have to be unique in the table 
        @param unique4ColumnList[list or tuple]: define the columns for which the column have to be unique, None(default), the parameter unique have to be TRUE!!! 
        @param insertIgnore[boolean]: use the ignore statement in the SQL statement, this will not raise an exception
        @param insertUpdate[boolean]: updates a row if primary key already exists, inserts if not
        @return: database identifier [int]
        """
        if filter4ColumnNames:
            colValList = self.filterColValDict4ColumnNames(table,colValDict)
        colValList = colValDict.items()
        primary_id = None
        if unique:
            if unique4ColumnList:
                whereStatement = " AND ".join([x[0] + ("=" if x[1] != None else " IS ") + self.escape4Sql(x[1]) for x in colValList if x[0] in unique4ColumnList])
            else:
                whereStatement = " AND ".join([x[0] + ("=" if x[1] != None else " IS ") + self.escape4Sql(x[1]) for x in colValList])
            getIdSql = "select id from %s%s where %s limit 1" % (self.defaultTablePrefix, table, whereStatement)
            #print getIdSql
            if self.cursor.execute(getIdSql):
                primary_id = self.cursor.fetchone()[0]
        if not primary_id or insertUpdate:
            cols = ",".join([x[0] for x in colValList])
            vals = ",".join([self.escape4Sql(x[1]) for x in colValList])
            ignore = "ignore" if insertIgnore else ""
            delayed = "delayed" if insertDelayed else ''
            sql = None
            if insertUpdate:
                colVals = ", ".join(['{}={}'.format(k,self.escape4Sql(v)) for k,v in colValList])
                sql = "insert %s into `%s%s` (%s) values (%s) on duplicate key update %s" % (delayed,self.defaultTablePrefix, table, cols, vals, colVals)
            else:
                sql = "insert %s %s into `%s%s` (%s) values (%s)" % (ignore,delayed,self.defaultTablePrefix, table, cols, vals)
            if printSql:
                print sql
            try:
                self.cursor.execute(sql)
                self.cursor.execute('Select last_insert_id()')
                primary_id = self.cursor.fetchone()[0] 
            except _mysql_exceptions.IntegrityError:
                try:
                    self.cursor.execute(getIdSql)
                    primary_id = self.cursor.fetchone()[0]
                except:
                    #print getIdSql
                    print sql," could not be executed"
                    print "Could also not get the primary key"
        return primary_id
    
    def getDate(self,entry):
        """Extract Year,Month and Day from entry (xmlElement or string) and format into SQL compatible string"""
        myDate = "0000-00-00"
        if type(entry)==lxml.etree._Element and  entry is not None:
            myDate = entry.find("Year").text + "-" + entry.find("Month").text + "-" + entry.find("Day").text
        elif type(entry)==str:
            myDate = re.sub("[^\d]","-",entry)
        return myDate


    def getAllPrimaryIds(self,table):
        """return all primary IDs from a table in the app"""
        table= self.defaultTablePrefix+table
        primaryKeyColumnName = mysql.get_primary_key(self.cursor, table)
        self.cursor.execute("Select %s from %s" % (primaryKeyColumnName,table))
        return [x[0] for x in self.cursor.fetchall()]

    def deleteWhitespacesLinebreaks(self,string):
        """* Replaces 2-n white spaces with 1
        * Replaces line breaks with 1 white space
        @param string: string to be changed 
        @return string free of white spaces and line breaks
        """
        if string is not None and type(string)==str:
            string = re.sub("\n\s*",' ',string.strip())
        return string 
    
    def disableKeys(self):
        for table in self.getTableNames():
            self.cursor.execute("ALTER TABLE " + table + " DISABLE KEYS")
        
    def enableKeys(self):
        for table in self.getTableNames():
            self.cursor.execute("ALTER TABLE " + table + " ENABLE KEYS")        
    
    def truncateTables(self,excludeTables=[]):
        """truncates all tables of adjango app, with parameter exclude a list of table names (without the app-prefix+'_') can be excludes"""
        tables = set(self.getTableNames())
        if type(excludeTables) in (list,tuple,set):
            excludeTablesWithPrefix = set([self.defaultTablePrefix+x for x in excludeTables])
            if len(excludeTablesWithPrefix-tables)==0: # checks if all excluded tables are present in app specific tables
                tables = tables - excludeTablesWithPrefix
        for table in tables:
            self.cursor.execute("truncate " + table)
            self.cursor.execute("ALTER TABLE %s AUTO_INCREMENT = 1" % table)
     
    def setWaitTime(self, TIMEOUT=86400):
        """* Since connection time out default is 8 hours (28800 seconds) and we have some long running imports
        it is useful to set the connection timeout to a higher value, here: 24 hours.
        @param timeOut: the timeOut in seconds (mysql allows 2147483 seconds for Windows machines and 31536000 seconds for other systems, default is 86400 sec.)"""
        self.cursor.execute("Set SESSION wait_timeout = %s" % TIMEOUT)

    def getTableNames(self):
        tablePrefix = self.defaultTablePrefix.replace("_","\\_")
        self.cursor.execute("show tables like '"+tablePrefix+"%'")
        return [x[0] for x in self.cursor.fetchall()]
    
    def noneIfEmpty(self,string):
        string = string.strip()
        return string if string else None
