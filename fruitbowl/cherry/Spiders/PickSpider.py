'''
.. module:: PickSpider
   :platform: Unix, OSX
   :synopsis: Scrapy spider object for crawling websites to extract dois and collect metadata

.. moduleauthor:: Patrick Lewis


'''
import scrapy
from Items import CherryItems
import re
import json
import datetime
import ScrapingTools
from scrapy import Request

class PickSpider(scrapy.Spider):
    '''Spider for visiting webpages and extracting dois and retrieving metadata'''
    name = "Pick"
    
    def __init__(self, *args, **kwargs):
        '''make a Pickspider
        
        Kwargs:
            start_urls (list): list of websites to visit
            allowed_domains (list): list of domains to constrain the spider to
                
        '''
        super(PickSpider, self).__init__(*args, **kwargs)
        self.start_urls = kwargs['start_urls']
        self.allowed_domains = set(kwargs['allowed_domains']+['api.crossref.org'])
        self.api_stub='http://api.crossref.org/works/'
    
    def start_requests(self):
        '''initialise and send requests for each url with relevant metadata'''
        total = len(self.start_urls)
        for url in self.start_urls:
            yield Request(url,
                callback=self.parse,errback=self.errback1)

    def parse(self, response):
        '''parse a webpage, collect dois, send requests to crossref for metadata collection
        
        Args:
            response (scrapy response): Scrapy Response object for the webpage
        Yields:
            scrapy requests to Crossref for extracted dois
        '''
		target_space = '//body'
		include_tags = True
		target = response.xpath(target_space).extract()[0]
		all_dois = ScrapingTools.find_dois(target) #extract the dois
		for doi in all_dois: #send request to crossref for each doi
			yield scrapy.Request(
				self.api_stub+doi,
				callback=self.parse_crossref,
				meta={'doi':doi,'source_url':response.url},
				errback=self.errback2
				)

    def parse_crossref(self,response):
        '''parse the message from crossref
        
        Args:
            response (scrapy Response): scrapy response object for message received from crossref
        
        Yields:
            item (CherryItems.CrossrefItem): partially complete article metadata to store
        '''
        message = json.loads(response.body_as_unicode())
        item = ScrapingTools.get_crossref_item(message['message'])
        item['crossref_doi']=True
        item['source_url']=response.meta['source_url']
        yield item
    
    def errback1(self,response):
    '''Error handling for failed url request
    
    Args:
        response (scrapy Response): scrapy response object for error message received from server
    
    Yields:
        item (CherryItems.BrokenItem): error reporting item
    
    '''
        item = CherryItems.BrokenItem()
        item['doi']=None
        item['error']={'404':'source'}
        item['source_url']=response.request.url
        yield item
        
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