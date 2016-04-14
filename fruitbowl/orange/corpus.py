'''
.. module:: corpus
   :platform: Unix, OSX
   :synopsis: corpus object for use in corpus manipulation

.. moduleauthor:: Patrick Lewis


'''
import fruitbowl.strawberry.sanitisers
from gensim import corpora
import corpus_stats
import codecs
import docIterators
import gensim
import random
import json

class Corpus(object):
    '''A Corpus represents a manipulation interface for operations for a text corpus
    generated from a scraping run from Cherry '''
    doc_iter=None
    dictionary=None
    inv_dict=None
    name='UNNAMED_CORPUS'
    statistics =None
    tfidf_model=None
    
    def __init__(self,name,doc_iter,dictionary=None,tfidf_model=None):
    '''Create a Corpus Object
    
    Args:
        name (str): The desired name of the corpus (Appears in dumps)
        doc_iter (docIterator): The :module:docIterator Object that streams the documents
            that make up the corpus
    
    Kwargs:
        dictionary (gensim.corpora.Dictionary): The tokenisation dictionary for the corpus. 
            Defaults to None if not specified and the dictionary is built from iterating the documents
        tfidf_model (gensim.models.tfidf_model): The tfidf model for the corpus. Defaults
            to None if not specified. Call :method: get_tfidf_model to build a tfidf model for a corpus
    '''
        self.doc_iter = doc_iter
        print('Building Dictionary')
        if dictionary:
            self.dictionary=dictionary
        else:#build a dictionary if one hasnt been provided
            iter_type=doc_iter.iter_type
            self.doc_iter.iter_type='SIMPLE'#stream word-by-word
            self.dictionary = corpora.Dictionary(doc_iter)
            self.doc_iter.iter_type=iter_type #return to what the iter_type was before
        #create an inverse dictionary to map from token to word
        self.inv_dict = {v:k for k,v in self.dictionary.iteritems()} 
        self.name=name
        if tfidf_model:
            self.tfidf_model=tfidf_model
    
    def rebuild_dicts(self):
        '''rebuild the dictionaries if the document corpus has changed'''
        self.doc_iter.iter_type='SIMPLE'
        self.dictionary = corpora.Dictionary(self.doc_iter)
        self.inv_dict = {v:k for k,v in self.dictionary.iteritems()}
        
    def get_bow_doc(self,sent):
        '''get the bag-of-words representation of a document/sentence
        
        Args: 
            sent (list): list of strings to return as bag-of-words representation
        
        Returns: 
            repr (list): list of (token (int), frequency (int)) tuples,
                the representation of inputted document in BOW space
        '''
        repr = self.dictionary.doc2bow(sent)
        return repr
    
    def generate_stats(self):
        '''Generate statistics about the corpus.
        '''
        self.statistics = corpus_stats(self.doc_iter,self.name)
    
    def get_tfidf_model(self):
        print('Creating TF-IDF Model')
        mod=gensim.models.TfidfModel(dictionary=self.dictionary)
        self.tfidf_model=mod
        return mod
    
    def get_tfidf_doc(self,sent):
        '''get the TF-IDF representation of a document/sentence
        
        Args: 
            sent (list): list of strings to return as TFIDF representation
        
        Returns: 
            repr (list): list of (token (int), weight (float)) tuples,
                the representation of inputted document in TF-IDF space
        '''
        try:
            repr= self.tfidf_model[self.get_bow_doc(sent)]
            return repr
        except:
            print('tfidf model must be built before representations can be generated')
        
    def export2jsonfile(self,file_name=None,tfidf=False):
        '''Export and save the corpus to disk as Json
        
        Kwargs:
            file_name (str): the name of the file to be produced. Defaults to None
                If filen_name is None, the produced file has the name of the corpus
            tfidf (bool): whether to export the corpus with tfidf weights
                defaults to False (do not include tfidf weights)
        
        The Exported json file includes everything from the document store the corpus streams from.
        if tfidf is chosen ,it also includes 'doc_weights' and 'sent_weights' for
        document tfidf weightings and sentence-by-sentence tfidf weightings 
        '''
        if file_name is None:
            file_name = self.name+'.json'
        if tfidf:
            if self.tfidf_model is None:
                self.tfidf_model=self.get_tfidf_model()
        with codecs.open(file_name,'w',encoding='utf8') as f:
            self.doc_iter.iter_type='EVERYTHING'
            for doc in self.doc_iter:
                if tfidf:
                    doc_weights=[]
                    sent_weights=[]
                    sents=doc['doc']
                    words=[word for sent in sents for word in sent]
                    #get doc tfidf weights
                    doc_tfidf=self.get_tfidf_doc(words)
                    doc_tfdict={k[0]:k[1] for k in doc_tfidf}
                    for i in range(len(doc['doc'])):
                        doc_weights.append([doc_tfdict[self.inv_dict[j]] for j in doc['doc'][i]])
                    #get sent tfidf weights
                    for sent in sents:
                        sent_tfidf=self.get_tfidf_doc(sent)
                        sent_tfdict={k[0]:k[1] for k in sent_tfidf}
                        weight=[sent_tfdict[self.inv_dict[word]] for word in sent]
                        sent_weights.append(weight)
                    doc['tfidf-weights']={'doc-weights':doc_weights,'sent-weights':sent_weights}
                ex = json.dumps(doc)
                f.write(ex+'\n')
        print('EXPORT COMPLETE')
    
    def get_sample(self,sample_size,return_type='DOI',doc_iter=None):
        '''Get a random sample of documents from the corpus
        
        Args:
            sample_size (int): the number of documents to include in the sample
        
        Kwargs:
            return_type (str): the iter_type to switch the document iterator to.
                In other words, what type of sample to return. Defaults to 'DOI', 
                which is {'doi':doi,'doc':list of sentence lists}
            doc_iter (docIterator): the docIterator to draw the sample from. Default to None.
                if doc_iter is None, it uses the Corpus object's docIterator
                
        Returns:
            sample (list): list of randomrecords from the corpus
        '''
        print('Sampling '+str(sample_size)+' random documents')
        randoms = random.sample(range(self.doc_iter.size), sample_size) #generate random integers
        sample=[]
        ind=0
        if doc_iter is None:#use own docIterator
           self.doc_iter.iter_type=return_type
           doc_iter=self.doc_iter
        for record in doc_iter:
            if ind in randoms:
                sample.append(record)
            ind+=1
        return sample
