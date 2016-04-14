'''
.. module:: fake_mongo
   :platform: Unix, OSX
   :synopsis: mock interface for mongodb for running locally when connections 
       to main database cannot be maintained
.. moduleauthor:: Patrick Lewis
'''
import json
import codecs


class FakeMongo(object):
    '''Mock Object interface for MongoDB client'''
    
    def __init__(self,file_name):
        '''Make a FakeMongo
        
        Args:
            file_name (str): name of json file to draw queries from
        '''
        with codecs.open(file_name,'r',encoding='utf8') as f:
            recs = json.load(f)
        self.recs=recs
    
    def find(self,query=None):
        '''perform query on file using mongodb query syntax (Only partially functional)
        
        Kwargs:
            query (dict): MongoDB style query
        
        Returns:
            fc (FakeCursor): iterator object for results of query'''
        if query==None:
            fc=FakeCursor(self.recs)
        else:
            retur = []
            k = query.keys()[0]
            v = query.values()[0]
            for rec in self.recs:
                if rec[k]==v:
                    retur.append(rec)
            fc=FakeCursor(retur)
        return fc

class FakeCursor(object):
    '''Iterator for results of a query to a FakeMongo Instance'''
    
    def __init__(self,values):
        '''create a FakeCursor
        
        Args:
            values (list): values for the cursor to return when iterated'''
        self.values=values
    
    def __iter__(self):
        '''Get the cursors values one by one
        
        Yields:
            v (object or primitive): one of the cursor's values
            
        '''
        for v in self.values:
            yield v
        
    def count(self):
        '''get the number of values in the cursor
        
        Returns:
            length (int): the number of values in the cursor
        '''
        length=len(self.values)
        return length