'''
.. module:: vect_generators 
   :platform: Unix, OSX
   :synopsis: classes for generating representation vectors from trained models

.. moduleauthor:: Patrick Lewis
'''
import numpy as np
import gensim.models
from abc import ABCMeta, abstractmethod,abstractproperty

class VectorGenerator(object):
    '''Abstract class for a representation Vector generating object'''
    __metaclass__=ABCMeta
   
    @abstractmethod
    def get_vector():
        '''Return a vector for a doi or sentence'''
        return None
    
    @abstractproperty
    def model():
        '''The model used in generating vectors'''
        return None
    @abstractproperty
    def dimensionality():
        '''The dimensionality of vectors returned by this VectorGenerator'''
        return None

class WordByWordGenerator(VectorGenerator):
    '''Implements VectorGenerator. Generates vectors that are 
    averaged word by word into document vector representations.
    '''
    model = {}
    dimensionality=0
    
    def __init__(self,model):
        '''Build a WordByWordGenerator.
        
        Args:
            model (gensim.models.Word2Vec or gensim.models.doc2vec.Doc2Vec): model from
                which to draw word component vectors from to aggregate with
        '''
        self.model=model
        self.dimensionality=model.vector_size
        
    def get_vector(self,doc,weights=None):
        '''Get a word-by-word averaged represenation vector for a document
        
        Args:
            doc (list): document that will be transformed into representation vector.
                format is list of lists of words [[word, word, ...],[word, word,...],...]
                        
        KWargs:
            weights (list): list of list of weights [[w, w, ...],[w, w,...],...] 
                corresponding to the weight of each word for weighted averaging of
                the word vectors into a document vector. Defaults to None, in 
                which case each word has equal weight, corresponding to 
                simple arithmentic mean
        
        Returns:
            doc_vec (numpy.array): document representation vector for inputted document
        
        '''
        acc=np.zeros(self.dimensionality)#create container for word vector sum
        divisor = 0
        doc = filter(lambda x: x != [], doc)#remove any empty sentences from document
        if weights is None:#if no weights provided, use unit weights
            weights = [[1. for w in s] for s in doc]
        sent_no = len(doc)
        for i in range(sent_no):
            sent = doc[i]
            weight= weights[i]
            for j in range(len(sent)):
                try:
                    acc+=weight[j]*(self.model[sent[j]])#accumulate vector sum
                    divisor+=weight[j]
                except:
                    pass
        if divisor==0:
            divisor=1. #stop division by zero
        doc_vec = acc/divisor #average
        return doc_vec

class SentBySentGenerator(VectorGenerator):
    '''Implements VectorGenerator. Generates vectors that are 
    averaged word by word into sentence vectors then
    averaged sentence by sentence into document vector representations.
    '''
    model = {}
    dimensionality=0
    
    def __init__(self,model):
        '''Build a SentBySentGenerator.
        
        Args:
            model (gensim.models.Word2Vec or gensim.models.doc2vec.Doc2Vec): model from
                which to draw word component vectors from to aggregate with
        '''
        self.model=model
        self.dimensionality=model.vector_size
        
    def get_vector(self,doc,weights=None):
        '''Get a sentence-by-sentence averaged represenation vector for a document
        
        Args:
            doc (list): document that will be transformed into representation vector.
                format is list of lists of words [[word, word, ...],[word, word,...],...]
        
        KWargs:
            weights (list): list of list of weights [[w, w, ...],[w, w,...],...] 
                corresponding to the weight of each word for weighted averaging of
                the word vectors into a document vector. Defaults to None, in 
                which case each word has equal weight, corresponding to 
                simple arithmentic mean
        
        Returns:
            doc_vec (numpy.array): document representation vector for inputted document
        
        '''
        acc=np.zeros(self.dimensionality)#create container for sentence vector sum
        divisor = 0
        doc = filter(lambda x: x != [], doc)#remove any empty sentences from document
        if weights==None:
            weights = [[1. for w in s] for s in doc]
        sent_no = len(doc)
        for i in range(sent_no):#get sentence vectors
            sent = doc[i]
            weight = weights[i]
            sent_acc=np.zeros(self.dimensionality)#create container for word vector sum
            sent_divisor=0
            for j in range(len(sent)):
                try:
                    sent_acc+=weight[j]*(self.model[sent[j]])#accumulate word vectors
                    sent_divisor+=weight[j]
                except:
                    pass
            if sent_divisor==0:
                sent_divisor=1 #stop division by zero
            acc+=(sent_acc/sent_divisor)
            divisor+=1
        if divisor==0:
            divisor=1. #stop division by zero
        doc_vec= acc/divisor
        return doc_vec

class Doc2VecGenerator(VectorGenerator):
    '''Implements VectorGenerator. Fetches vectors from doc2vec model
    '''
    model = {}
    dimensionality=0
     
    def __init__(self,model):
        '''Build a Doc2VecGenerator model
        
        Args:
            model (gensim.models.doc2vec.Doc2Vec) : model from which to draw
                document vectors from'''
        self.model=model
        self.dimensionality=model.vector_size
     
    def get_vector(self,doi):
        '''get representation vector for document with doi
        
        Args:
            doi (str): doi for desired document
        
        Returns:
            doc_vec (numpy.array): representation vector for desired document 
        '''
        doc_vec= self.model.docvecs[doi]
        return doc_vec
     
  

        
        
        
