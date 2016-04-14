'''
.. module:: docIterators 
   :platform: Unix, OSX
   :synopsis: docIterators is a collection of objects used for streaming records from the
       data source in a memory-friendly way

.. moduleauthor:: Patrick Lewis
'''
from abc import ABCMeta, abstractmethod,abstractproperty
import codecs
import json
import sys
import pymongo
from pymongo import MongoClient
import fruitbowl.strawberry.sanitisers
import gensim

def progress(ind,size):
    '''Prints a Progress Bar for a Document Iterator to the command line
    
    Args:
        ind (int): the index of the current record
        size (int): the maximum possible record
    '''
    percent = int(100*float(ind)/size)
    sys.stdout.write('\r[{0}{1}] {2}% {3}'.format('#'*(percent/10),' '*(10-percent/10), percent, ind))
    sys.stdout.flush()
    
class DocumentIter(object):
    '''Abstract class for all DocumentIter objects to implement
    '''
    __metaclass__ = ABCMeta
    
    @abstractproperty
    def source(): 
        '''The data source for the records'''
        return None
    
    @abstractproperty
    def size():
        '''Number of records in the datastore'''
        return None
    
    @abstractmethod
    def __iter__():
        '''yield the records one-by-one'''
        yield None
    
    @abstractproperty   
    def sanitiser():
        '''The sanitiser object used to clean the documents in streaming'''
        return None
    
    @abstractproperty
    def iter_type():
        '''The format to yield the records as''' 
        return 'SIMPLE'
    
class SimpleDiskIter(DocumentIter):
    '''Implements DocumentIter for file on disk, each line containing a document of words
    
    Implemented iter_types:
        'SIMPLE': yields [word, word, word...] for each record
    '''
    size=0
    source=''
    sanitiser=None
    iter_type='SIMPLE'

    def __init__(self,txf,sanit=None):
        '''Build a SimpleDiskIter
        
        Args:
            txf (str): the text file data source
            
        Kwargs:    
            sanit (Stawberry.sanitiser.Sanitiser): The sanitiser to use in streaming 
                from data source. (Defaults to None, and uses a NullSanitiser )
        '''
        self.source=txf
        if sanit:
            self.sanitiser=sanit
        else: #if no sanitiser specified, use a NullSanitiser
            self.sanitiser=sanitisers.NullSanitiser()
        ind=0
        for line in codecs.open(txf,'r',encoding='utf8'):#count the number of records
            ind+=1
        self.size=ind

    def __iter__(self):
        '''Iterate over the DocumentIterator
        
        Yields:
            doc (list or dict): the record to return (list of words)  
        '''
        for line in codecs.open(self.source,'r',encoding='utf8'):
            if ind%1000==0:
                progress(ind,self.size)
            doc = self.sanitiser.sanitise(line).split()
            yield doc
            
class JsonDiskIter(DocumentIter):
    '''Implements DocumentIter for a json file on disk containing a list of records.
    
    Implemented iter_types:
        'SIMPLE': yields [word, word, word...] for each record
        'SENTENCES': yields [word, word,...] for each sentence in each record
        'DOI': yields {'doi':doi,'doc':[[w,w...][w,w...],...]} for each record
        'LABELED_SENTENCES': yields a gensim.models.doc2vec.LabeledSentence for
            each sentence in each record
        'VECTORS': yields {'doi':doi,'vectors':vectors} for each record. Vectors
            is usually a dictionary of different vector representations.
        'EVERTYTHING': yields dict with everything found in the datasource per record
    '''
    size=0
    source=''
    sanitiser=None
    iter_type='SIMPLE'
    
    def __init__(self,txf,sanit=None,iter_type='SIMPLE'):
        '''build a JsonDiskIter
        
        Args:
            txf (str): the json list file data source
            
        Kwargs:
            sanit (Stawberry.sanitiser.Sanitiser): The sanitiser to use in streaming 
                from data source. (Defaults to None, and uses a NullSanitiser)
            iter_type (str): defaults to 'SIMPLE', string specifying return type
            
        the textfile txf json list requires each entry to hav keys:
            1) 'doc' OR 'title' and 'abstract'
            2) 'doi'
            3) 'vectors' if using 'VECTORS' as iter_type
        '''
        self.source=txf
        if sanit:
            self.sanitiser=sanit
        else: #if no sanitiser specified, use a NullSanitiser
            self.sanitiser=fruitbowl.strawberry.sanitisers.NullSanitiser()
        ind=0
        for line in codecs.open(txf,'r',encoding='utf8'): #count the number of records
            ind+=1
        self.size=ind
        self.iter_type=iter_type
        
    def __iter__(self):
        '''Iterate over the DocumentIterator
        
        Yields:
            export (list or dict): the record to return (dependent on iter_type) 
        '''
        ind=0
        for line in codecs.open(self.source,'r',encoding='utf8'):
            if line[0]=='[':#first line in file
                line=line[1:].strip(',')
            if line[-1]==']':#last line in file
                line=line[:-1]
            else:
                line=line[:-1].strip(',')#remove ending comma
            record = json.loads(line)
            if record.has_key('doc'):#already has a doc field
                doc=record['doc']
            else: #create doc field
                title = record['title']
                abstract_sents = record['abstract'].split('. ')
                doc =[]
                doc.append(self.sanitiser.sanitise(title).split())
                san_abs=[]
                for sent in abstract_sents:
                    doc.append(self.sanitiser.sanitise(sent).split())
            ind+=1
            doi=record['doi']
            if ind%1000==0:
                progress(ind,self.size)
            #yield result based on iter_type
            if self.iter_type=='DOC':
                export=doc
                yield export
            elif self.iter_type=='SIMPLE': 
                export = [word for sent in doc for word in sent]
                yield export
            elif self.iter_type=='SENTENCES':
                for sent in doc:
                    export=sent
                    yield export
            elif self.iter_type=='DOI':
                yield {'doi':record['doi'],'doc':doc}
            elif self.iter_type=='LABELED_SENTENCES':
                for sent in doc:
                    export = gensim.models.doc2vec.LabeledSentence(sent,tags=[doi])
                    yield export
            elif self.iter_type=='VECTORS':
                export= {'doi':record['doi'],'vectors':record['vectors']}
                yield export
            elif self.iter_type=='EVERYTHING':
                record['doc']=doc
                export=record
                yield export
            else:
                pass
        print('\n')
            
class MemoryIter(DocumentIter):
    '''Implements DocumentIter for data store list in memory
    
    Implemented iter_types:
        'SIMPLE': yields [word, word, word...] for each record
    '''
    size=0
    source=[]
    sanitiser=None
    iter_type="SIMPLE"
    
    def __init__(self,source,sanit=None):
         '''Build a MemoryIter
        
        Args:
            txf (str): the list in memory to iterate over
            
        Kwargs:    
            sanit (Stawberry.sanitiser.Sanitiser): The sanitiser to use in streaming 
                from data source. (Defaults to None, and uses a NullSanitiser )
        '''
        self.size = len(source)
        self.source=source
        if sanit:
            self.sanitiser=sanit
        else: 
            self.sanitiser=sanitisers.NullSanitiser()
        
    def __iter__(self):
        '''Iterate over the DocumentIterator
        
        Yields:
            export (list or dict): the record to return (dependent on iter_type) 
        '''
        ind=0
        for record in self.source:
            ind+=1
            if ind%1000==0:
                progress(ind,self.size)
            export = [self.sanitiser(record).split()]
            yield export
        print('\n')
        
class MongoIter(DocumentIter):
    '''Implements DocumentIter for a MongoDB database collection.
    
    Implemented iter_types:
        'SIMPLE': yields [word, word, word...] for each record
        'SENTENCES': yields [word, word,...] for each sentence in each record
        'DOI': yields {'doi':doi,'doc':[[w,w...][w,w...],...]} for each record
        'LABELED_SENTENCES': yields a gensim.models.doc2vec.LabeledSentence for
            each sentence in each record
        'VECTORS': yields {'doi':doi,'vectors':vectors} for each record. Vectors
            is usually a dictionary of different vector representations.
        'EVERTYTHING': yields dict with everything found in the datasource per record
    '''
    size=0
    source=''
    sanitiser=None
    iter_type='SIMPLE'
    
    def __init__(self,db_conn,query=None,sanit=None,iter_type='SIMPLE',from_list=None):
        '''build a MongoIter
        
        Args:
            db_conn (list): [mongourl (str),database_name(str),collection_name(str)]
            
        Kwargs:
            query (dict): MonogDB query (defaults to None, resulting in whole dataset
                being streamed)
            sanit (Stawberry.sanitiser.Sanitiser): The sanitiser to use in streaming 
                from data source. (Defaults to None, and uses a NullSanitiser)
            iter_type (str): defaults to 'SIMPLE', string specifying return type
            from_list (list): list of dois to stream data from (alternative to query)
                defaults to None (query  keyword is used)
            
        the MongnoDb document must have fields:
            1) 'doc'
            2) 'doi'
            3) 'vectors' if using 'VECTORS' as iter_type
        '''
        if sanit:
            self.sanitiser=sanit
        else:
            self.sanitiser=sanitisers.NullSanitiser()
        self.source=MongoClient(db_conn[0])[db_conn[1]][db_conn[2]]
        self.query=query
        self.size=self.source.find(query).count()
        self.iter_type=iter_type
        self.from_list=from_list
    
    def __iter__(self):
        ind=0
        if self.from_list is None: #use query
            for record in self.source.find(self.query):
                doc = record['doc']
                doi = record['doi']
                ind+=1
                if ind%1000==0:
                    progress(ind,self.size)
                if self.iter_type=='DOC':
                    yield doc
                elif self.iter_type=='SIMPLE': 
                    yield [word for sent in doc for word in sent]
                elif self.iter_type=='SENTENCES':
                    for sent in doc:
                        yield sent
                elif self.iter_type=='DOI':
                    yield {'doi':record['doi'],'doc':doc}
                elif self.iter_type=='LABELED_SENTENCES':
                    for sent in doc:
                        yield gensim.models.doc2vec.LabeledSentence(sent,tags=[doi])
                elif self.iter_type=='VECTORS':
                    yield {'doi':doi,'vectors':record['vectors']}
                else:
                    pass
        else: #use list of requested dois
            for doi in self.from_list:
                record=self.source.find_one({'doi':doi})
                if record is not None:
					doc=record['doc']
					ind+=1
					if ind%10==0:
						progress(ind,len(self.from_list))
					if self.iter_type=='DOC':
						yield doc
					elif self.iter_type=='SIMPLE': 
						yield [word for sent in doc for word in sent]
					elif self.iter_type=='SENTENCES':
						for sent in doc:
							yield sent
					elif self.iter_type=='DOI':
						yield {'doi':record['doi'],'doc':doc}
					elif self.iter_type=='LABELED_SENTENCES':
						for sent in doc:
							yield gensim.models.doc2vec.LabeledSentence(sent,tags=[doi])
					elif self.iter_type=='VECTORS':
						yield {'doi':doi,'vectors':record['vectors']}
					elif self.iter_type=='EVERYTHING':
					    yield record
					else:
						pass
        print('\n')

    def get_record(self,doi):
        '''get single record
        Args:
            doi (str): doi of record to return
        
        Returns:
            export (dict): mongodb document of requested doi
        '''
        export= self.source.find_one({'doi':doi})  
        return export