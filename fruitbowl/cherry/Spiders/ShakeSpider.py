'''
.. module:: ShakeSpider
   :platform: Unix, OSX
   :synopsis: Scrapy spider object for retrieving metadata for dois from list of dois

.. moduleauthor:: Patrick Lewis


'''
import scrapy
from Items import CherryItems
import re
import json
import datetime
import ScrapingTools
from scrapy.http import Request

class ShakeSpider(scrapy.Spider):
    '''Spider for retrieving metadata for inputted dois'''

    name = "Shake"
    
    def __init__(self, *args, **kwargs):
        '''make a shakespider
        
        Kwargs:
            dois (list): list of dois to extract metadata from
            doi_sources (list): list of source websites the dois have originated from
            
        Yields:
            scrapy Requests to Crossref to get doi metadata
        '''
        super(ShakeSpider, self).__init__(*args, **kwargs)
        self.start_urls = ['http://api.crossref.org/works/'+d for d in kwargs['dois']]
        self.allowed_domains = ['api.crossref.org']
        self.doi_sources = kwargs['doi_sources']
        
    def start_requests(self):
        '''initialise and send requests'''
        total = len(self.start_urls)
        for url in self.start_urls:
            doi = url.replace('http://api.crossref.org/works/','')
            yield Request(url, meta={'doi': doi,'source_url':self.doi_sources[doi]},
                callback=self.parse,errback=self.errback2)
    
    def parse(self,response):
        '''parse the message from crossref
        
        Args:
            response (scrapy Response): scrapy response object for message received from crossref
        
        Yields:
            item (CherryItems.CrossrefItem): partially complete article metadata to store
        '''
        message = json.loads(response.body_as_unicode())
        item = CrossRefTools.get_crossref_item(message['message'])
        item['crossref_doi']=True
        item['source_url']=response.meta['source_url']
        print('Doi scraped')
        yield item
        else:
            item = CherryItems.BrokenItem()
            item['doi']=doi
            item['error']='broken_doi'
            item['soruce_url']=response.meta['source_url']
            print('Lost record')        

    def errback2(self,response):
        '''Error handling for failed request to crossrefs
        
        Args:
            response (scrapy Response): scrapy response object for error message received from server
        
        Yields:
            request to crossref agency api
        '''
        yield scrapy.Request(
            self.api_stub+response.request.meta['doi']+'/agency',
            meta=response.request.meta,callback=self.check_doi,
            errback=self.errback3)

    def errback3(self,response):
        '''Error handling for when a doi doesnt exist
        
        Args:
            response (scrapy Response): scrapy response object for error message received from server
        
        Yields:
            item (CherryItems.BrokenItem): error reporting item
        '''
        item = CherryItems.BrokenItem()
        item['doi']=response.request.meta['doi']
        item['error']={'broken_doi':response.request.meta['doi']}
        item['source_url']=response.request.meta['source_url']
        yield item
    
    def check_doi(self,response):
    '''check for the existence of a doi 
    
    Args:
        response (scrapy Response): scrapy response object for  message received from crossref agency api
    
    Yields:
        item (CherryItems.CrossRefItem): uncompleted metadata for article for doi not indexed by crossref
    '''
        doi = response.meta['doi']
        item = CherryItems.CrossRefItem()
        item['doi']=doi
        item['crossref_doi']=False
        item['source_url']=response.meta['source_url']
        yield item