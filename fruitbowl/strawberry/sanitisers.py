'''
.. module:: sanitisers 
   :platform: Unix, OSX
   :synopsis: classes for data sanitation of scraped language
.. moduleauthor:: Patrick Lewis
'''

from abc import ABCMeta, abstractmethod,abstractproperty
import json
import re
import codecs
import nltk.stem

class Sanitiser(object):
    '''Abstract class for all Sanitiser objects to implement'''
    __metaclass__=ABCMeta
    @abstractmethod
    def sanitise():
        '''Sanitise the inputted sentence'''
        return None
    
    def remove_unicode_punct(self,sentence, chars):
        '''remove punctuation from a sentence
        
        Args:
            sentence (str): sentence to remove punctuation from
            chars (list): list of punctuation characters to remove
            
        Returns:
            scrubbed (str): sentence with punctuation removed
        '''
        scrubbed=re.sub(u'(?u)[' + re.escape(''.join(chars)) + ']', ' ', sentence)
        return scrubbed

class NullSanitiser(Sanitiser):
    '''implementation of Sanitiser that just acts as a wrapper.
    
    Does not perform any sanitation
    '''
        
    def sanitise(self,sentence):
        '''implements Sanitiser.Sanitise
        
        Args:
            sentence (str): sentence to sanitise
        
        Returns:
            export (str): exported sentence. Idenitical to inputted sentences.
        '''
        export = sentence
        return export

class MinimalSanitiser(Sanitiser):
    '''Implementation of Sanitiser, casts to lower case and removes punctuation.'''
    
    def __init__(self,punct_file):
        '''Build a MinimalSanitiser
        
        Args:
            punct_file (str): json file containing list of characters to remove
        '''
        with codecs.open(punct_file,'r',encoding='utf8') as f:
            self.punct_filter = json.load(f)#load punctuation to filter
    
    def sanitise(self,sentence):
        '''implements Sanitiser.Sanitise. remove punctuation characters from sentence
        
        Args:
            sentence (str): sentence to sanitise
        
        Returns:
            export (str): sentence with punctuation removed
        
        Process:
            1) cast to lower case
            2) remove whitespace and newlines
            3) remove unwanted punctuation
        '''
        lt = sentence.lower()
        slt = lt.strip()
        tslt = self.remove_unicode_punct(slt,self.punct_filter)
        export = u' '.join(tslt.strip().split())
        return export
    
class StopWordSanitiser(Sanitiser):
    '''Implementation of Sanitiser, removes stopwords and punctuation from sentences'''
    def __init__(self,stopwords_file,punct_file):
        '''build a StopWordSanitiser
        
        Args:
            stopwords_file (str): json file containing list of stopwords to remove
            punct_file (str): json file containing list of characters to remove
        '''
        with codecs.open(stopwords_file,'r',encoding='utf8') as f:
            self.stopwords = json.load(f)#load stopwords
        with codecs.open(punct_file,'r',encoding='utf8') as f:
            self.punct_filter = json.load(f)#load characters to remove
    
    def sanitise(self,sentence):
        '''implements Sanitiser.Sanitise. remove characters and stopwords from sentence
        
        Args:
            sentence (str): sentence to sanitise
        
        Returns:
            export (str): sentence with punctuation removed, and stopwords removed
        
        Process:
            1) cast to lower case
            2) remove whitespace and newlines
            3) remove unwanted punctuation
            4) remove stopwords    
        '''
        lt = sentence.lower()
        slt = lt.strip()
        tslt = self.remove_unicode_punct(slt,self.punct_filter)
        stop_filtered = [i for i in tslt.split() if i not in self.stopwords]
        export = u' '.join(stop_filtered)
        return export

class StemmingSanitiser(Sanitiser):
    '''Implementation of Sanitiser, removes stopwords and punctuation
     from sentences and stems words using one of four stemming algorithms 
     from NLTK.'''

    def __init__(self,stopwords_file,punct_file,stem_type='SNOWBALL'):
        '''Build a StemmingSanitiser 
        
        Args:
            stopwords_file (str): json file containing list of stopwords to remove
            punct_file (str): json file containing list of characters to remove
        
        Kwargs:
            stem_type (str): 'SNOWBALL' or 'PORTER' or 'LANCASTER' or 'WORDNET'
                specify 1 of 4 stemming algorithms to use in stemming.
                Defaults to 'SNOWBALL'
        '''
        with codecs.open(stopwords_file,'r',encoding='utf8') as f:
            self.stopwords = json.load(f)
        with codecs.open(punct_file,'r',encoding='utf8') as f:
            self.punct_filter = json.load(f)
        self.stem_type=stem_type
        if stem_type=='SNOWBALL':
            self.stemmer = nltk.stem.snowball.EnglishStemmer()
        elif stem_type=='PORTER':
            self.stemmer = nltk.stem.PorterStemmer() 
        elif stem_type=='LANCASTER':
            self.stemmer = nltk.stem.LancasterStemmer()
        elif stem_type=='WORDNET':
            self.stemmer = nltk.stem.WordNetLemmatizer()
        else:
            print('Unrecognised Stemming Algorithm Requested')
            print('Reverting to Default SNOWBALL stemmer')
            self.stemmer = nltk.stem.snowball.EnglishStemmer()
    
    def sanitise(self,sentence):
        '''implements Sanitiser.Sanitise. Remove characters and stopwords from sentence
           and stems words to their root words
        
        Args:
            sentence (str): sentence to sanitise
        
        Returns:
            export (str): sanitised sentence
        
        Process:
            1) cast to lower case
            2) remove whitespace and newlines
            3) remove unwanted punctuation
            4) remove stopwords 
            5) Perform Stemming on surviving words   
        '''
        lt = sentence.lower()
        slt = lt.strip()
        tslt = self.remove_unicode_punct(slt,self.punct_filter)
        stop_filtered = [i for i in tslt.split() if i not in self.stopwords]
        if self.stem_type=='WORDNET':
            stem_filtered = [self.stemmer.lemmatize(i) for i in stop_filtered]
        else:
            stem_filtered = [self.stemmer.stem(i) for i in stop_filtered]
        export = u' '.join(stem_filtered)
        return export
    