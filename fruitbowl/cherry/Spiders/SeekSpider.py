'''
.. module:: SeekSpider
   :platform: Unix, OSX
   :synopsis: Scrapy spider object for crawling websites to extract dois

.. moduleauthor:: Patrick Lewis


'''
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from Items import CherryItems
import re
import scrapingtools

class SeekSpider(CrawlSpider):
    '''Spider for crawling webistes to extract dois
    
    '''
    name = 'Seek'
    rules = (Rule(LinkExtractor(allow=()), callback='parse_obj', follow=True),)
    
    def __init__(self, *args, **kwargs):
        ''' Create a SeekSpider
        
        Kwargs:
            start_urls (list): list of urls to start scraping with.
            allowed_domains (list):list of domain names to limit scraping to
            
        
        '''
        super(SeekSpider, self).__init__(*args, **kwargs)
        self.start_urls = kwargs['start_urls']
        self.allowed_domains = kwargs['allowed_domains']
        #create rules for spider
        SeekSpider.rules = ( Rule (LinkExtractor(allow=[self.allowed_domains]), callback='parse_obj', follow=True),)
        #compile the Rules
        super(SeekSpider, self)._compile_rules()
    
    def parse_obj(self,response):
        '''parse a webpage and collect any dois on the page
        
        Args: 
            response (Scrapy Response object): the response object for the current webpage
        
        Yields: 
            item (Cherry.Items.SeekItem): scrapy item object for storage if dois found on the page
        '''
        #process the page body to find dois
        dois = scrapingtools.find_dois(response.xpath('//body').extract()[0])
        #yield the url if dois were found on page
        if not(dois==[]):
            item = CherryItems.SeekItem()
            item['url'] = response.url
            item['num_dois'] = len(dois)
            yield item