'''
.. module:: scrapingtools
   :platform: Unix, OSX
   :synopsis: Function library for use in Cherry module scraping
.. moduleauthor:: Patrick Lewis


'''
from Items import CherryItems
import datetime
import json
import re
import os
import pickle

def get_settings():
    '''load Scrapy settings from pickled state in 'settings.txt'
    
    Returns:
        settings (Scrapy.Settings): A scrapy settings object picked to a text file
    '''
    with open('settings.txt','r') as f:
        settings = pickle.load(f)
    return settings

def finalise_file(file_name):
    '''Make a json document list built item-by-item legal and final by appending ']'
    
    Args:
        file_name (str): The name of the file to finalise
    '''
    with open(file_name,'rb+') as f:
        f.seek(-2, os.SEEK_END)
        f.truncate()
        f.write(']')

def initialise_file(file_name):
    '''Create a json list file ready to be streamed json objects.
    
     Creates file and writes '[' ready for first json serialised object to directly append to
     
     Args:
         file_name (str): the name of the json file to create
     '''
    with open(file_name,'wb+') as f:
        f.write('[')

def find_dois(txt):
    '''return list of DOIs in free text
    
    uses regex modified from http://stackoverflow.com/questions/27910/finding-a-doi-in-a-document-or-page
    Alix Axel's regex, with modifications http://stackoverflow.com/users/89771/alix-axel
    
    Args:
        txt (str): text corpus to search for dois in
    
    Returns:
        dois (list): list of doi strings found in text
        
    '''
    doi_re = re.compile(r'\b(10[.][0-9]{3,}(?:[.][0-9]+)*/(?:(?!["&\'()])\S)+)')
    all_dois = doi_re.findall(txt)
    cleans =  [clean_doi(d) for d in all_dois]
    dois = list(set(cleans)) #uniqify
    return dois
    
def clean_doi(d):
    '''Clean a doi identified by regex pattern matching by removing html tags, commas etc
    
    Args:
        d (str): doi string with html tags attached
    
    Returns:
        clean (str): cleaned doi string
    '''
    if d[-1] in ['.',',']:#remove trailing dots or commas (empirical rule)
        d=d[:-1] 
    clean = re.sub(r'<[^>]+>$','',d)#strip trailing html tags
    clean = re.sub(r'<.*?>','',d)
    return clean 
     
def dump_record(self,record,file_name):
    '''json serialise a scraped record and write it to json list file
    
    Args:
        record (object or primitive): anything json-serialisable to write to file
        file_name (str): name of json file to write serialised record to
    '''
    with open(file_name,'a') as f:
        ln = json.dumps(record,f) + ',\n' #serialise, add comma and newline (assumes writing to list)
        f.write(ln)

def get_author(auth):
    '''Normalise the form of a scraped author name
    
    handles various cases of author names and maps them to format 'ABC Lastname'
    
    Args:
        auth (dict): author information recieved from crossref api
    
    Returns:
        clean (str): normalised author name
    '''
    clean_given = ''
    family = ''
    kys = auth.keys()
    if 'given' in kys:
        given = auth['given']
        clean_given = ''.join([i[0] for i in given.strip().split(' ')])
    if 'family' in kys:
        family = auth['family']
    clean=(clean_given+' '+family).strip()
    return clean

def get_aff(auth):
    '''Normalise form of scraped affiliations
    
    Handles various formats of affiliations scraped from crossref, maping them to a list
    
    Args:
        auth (dict): author information recieved from crossref api
        
    Returns:
        affs (list): list of strings of affiliations for author
     '''
    affs = []
    for aff in auth['affiliation']:
        affs.append(aff['name'])
    return affs

def get_journal(journal_list):
    '''Helper function for :func:get_crossref_item 
    
    Args: 
        journal_list (list): list of journals an article was published in (usually length is 0 or 1)
    
    Returns:
        journal (str): first journal in journal_list or None if length is zero
    '''
    if len(journal_list)>0:
        journal = journal_list[0]
    else:
        journal = None
    return journal
    

def get_date(mess):
    '''Get and Normalise the Earliest date of publication from message recieved from crossref
    
    Args:
        mess (dict): message recieved from crossref API for particular doi
    
    Returns:
        pub_date (Datetime): the earliest date in the record, wrapped in datetime object
    
    '''
    #possible fields with dates:
    date_keys = ['published-online',
                 'deposited',
                 'indexed',
                 'published-print',
                 'created',
                 'issued'
                ]
    dates = []
    for dk in date_keys:#collect dates
        if dk in mess.keys():
            if mess[dk] and mess[dk]['date-parts'][0][0]:
                dates.append(mess[dk]['date-parts'][0])
    pub_dates = []
    for ymd in dates:#normalise dates by casting to datetime obj
        if len(ymd)==1:
            pub_dates.append(datetime.datetime(ymd[0],1,1))
        if len(ymd)==2:
            pub_dates.append(datetime.datetime(ymd[0],ymd[1],1))
        if len(ymd)==3:
            pub_dates.append(datetime.datetime(ymd[0],ymd[1],ymd[2]))
    pub_date = min(pub_dates)#return the earliest date
    return pub_date

def get_crossref_item(mess):
    '''create :class:CherryItems.CrossRefItem from message recieved from crossref
    
    Args:
        mess (dict): message recieved from Crossref API for particular doi
        
    Returns:
        item (CherryItem.CrossRefItem): populated partially complete metadata for article
    '''
    auths=[]
    affs = []
    if 'author' in mess.keys(): #get and normalise authors and affiliations
        for auth in mess['author']:
            auths.append(get_author(auth))
            aff = get_aff(auth)
            affs+=aff
        affs = list(set(affs))
    pub_date = get_date(mess) #get publication date
    titles=[]
    for tit in mess['title']:
        titles.append(tit) #get all the titles the article was published under
    e_doi = mess['DOI']
    e_authors = ', '.join(auths) #serialise authors for export
    try:
        e_date = pub_date.strftime('%d %B %Y')#try to cast the date to exportable format
    except:
        e_date = '01 January 1900'#error handling date for broken date collection
    e_title = ". ".join(titles) 
    e_pub = mess['publisher']
    e_journal = get_journal(mess['container-title'])
    e_abstract = 'PENDING'
    e_affs = '; '.join(affs)
    item = CherryItems.CrossRefItem() #create item and populate
    item['doi'] = e_doi
    item['title'] = e_title
    item['authors'] = e_authors
    item['affiliations'] = e_affs
    item['date'] = e_date
    item['publisher'] = e_pub
    item['journal'] = e_journal
    return item