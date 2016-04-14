'''
.. module:: MunchSpider
   :platform: Unix, OSX
   :synopsis: Scrapy spider object for collecting metadata from publisher webpages

.. moduleauthor:: Patrick Lewis


'''
import scrapy
import Items.CherryItems
import re
from pymongo import MongoClient
import sys
from scrapy.spiders import CrawlSpider
from scrapy.http import Request
import traceback
from twisted.internet.error import TimeoutError

class MunchSpider(CrawlSpider):
    '''
    MunchSpider scrapy crawlspider parses a list of dx.doi.org/<doi>
    links to extract metadata from publishers
    '''
    name = "Munch"
    losses = 0
    progress = 0

    def __init__(self, *args, **kwargs):
        '''Create a MunchSpider
        
        Kwargs:
            start_urls (list): list of dx.doi.org/<doi> links to visit
            allowed_domains (list): list of allowed domains the spider may visit
            publisher_database (object): either a mongodb client of Fake_mongo interface
                                         that when queried, gives xpaths to publisher webpage
            crossref_items (dict) = partially resolved doi metadata items
        '''
        super(MunchSpider, self).__init__(*args, **kwargs)
        self.start_urls = kwargs['start_urls']
        self.allowed_domains = kwargs['allowed_domains']
        self.publisher_database = kwargs['publisher_database']
        self.crossref_items = kwargs['crossref_items']
        
    def get_pub_paths(self,publisher):
        '''Get xpaths for a specified publisher website 
        
        Args:
            publisher (str): website of publisher to query database on 
            
        Returns:
            publishers_iterator (iterator): iterator that contains xpaths to try for current publisher 
        '''
        publishers_iterator = self.publisher_database.find({'pub_website':publisher})
        if self.publisher_database.find({'pub_website':publisher}).count()==0:
            raise Exception('no publisher website found') 
        return publishers_iterator

    def choose_items(self,itemlist):
		'''return most plausable item from a list of possible resolved items 
		
		Args:
		    itemlist (list): list of CherryItems.CompleteItem objects
		
		Returns:
		    best_item (CherryItems.Complete_Item): item in itemlist with most completed fields
		'''
		scores=[]
		for it in itemlist: #score each item
			score = 0
			for k,v in it.items():
				if type(v)==str:
					if not(v.strip()==u''): score+=1 #increment score if not blank string
				elif type(v)==list:
					if len(v)>0: score+=1 #increment score if not empty list
			scores.append(score)
		best_item=itemlist[scores.index(max(scores))] #choose highest scoring item
		return best_item
    
    def start_requests(self):
    '''initialise and send requests for each url with relevant metadata'''
        for url in self.start_urls:
            doi = url.replace('http://dx.doi.org/','') #get the doi
            yield Request(url, meta={'doi': doi,'crossref_item':self.crossref_items[doi]},
                callback=self.parse,errback=self.errback1)
    
    def errback1(self,response):
        '''Handle request error for redirection to publisher websites
        Args:
            response (Scrapy Response): failure message
        
        Returns:
            item (CherryItems.BrokenItem): failed collection item detailing failure
        '''
		item = Items.CherryItems.BrokenItem()
		item['doi']=response.request.meta['doi']
		item['source_url']=response.request.meta['crossref_item']['source_url']
		item['error']={'404':'publisher'}
		yield item
    
    def parse(self, response):
        '''parse publisher webpage and extract article metadata
        
        Args: 
            response(Scrapy Response): scrapy response object for recieved webpage
        
        Yields:
            item (CherryItems.CompleteItem or BrokenItem): succefully resolved record
                or error reporting item if error in collection unrecoverable
        '''
        self.progress+=1 #increment the progress counter
        pub=response.url.split('/')[2] #get the publisher domain
        try:
            publisher_iterator = self.get_pub_paths(pub) #get the xpaths to try scraping with
            failed_request=False 
        except: #handle failing to get the xpaths (no xpaths for this publisher)
            failed_request=True 
            item = Items.CherryItems.BrokenItem()
            item['doi']=response.meta['doi']
            item['source_url']=response.meta['crossref_item']['source_url']
            item['error']={'missing_pub':pub}
            yield item #yield error reporting item
            self.losses+=1
        if not failed_request: 
            itemlist = []
            for paths in publisher_iterator:
                try: #try to use current xpath set to create item
                    item=self.get_item(response,paths)
                    itemlist.append(item)
                except:#recover if this fails
                    traceback.print_exc(file=sys.stdout) 
                    pass
            try: #get most complete item, successfully yield it 
                item = self.choose_items(itemlist)
                yield item
            except: #recover by yielding error reporting item
                item = Items.CherryItems.BrokenItem()
                item['doi']=response.meta['doi']
                item['source_url']=response.meta['crossref_item']['source_url']
                item['error']={'collection':pub}
                yield item
                self.losses+=1
    
    def get_item(self, response, paths):
        ''' get complete metadata from publisher webpage
        
        Args: 
            response (Scrapy Response): scrapy response object for current page
            paths (list): Xpaths to extract meta data
        
        Returns:
            item (CherryItems.CompleteItem): complete metadata for associated article 
        '''
        abstract = response.xpath(paths['x_abstract']).extract()[0]
        try: #try to get affiliations (rarely works)
	    depts = response.xpath(paths['x_depts'])
            dex=[]
            for sdept in depts:
                d = dept.xpath(paths['x_dept']).extract()
                if not(d==[]):
                    dex.append(d[0])
            dex = list(set(dex))
        except:#return empty affiliations
	        dex = []
	    #create the item
        item = Items.CherryItems.CompleteItem()
        protoitem = response.meta['crossref_item']
        item['doi'] = protoitem['doi']
        item['title'] = protoitem['title']
        item['abstract'] = re.sub('\n','',abstract)
        item['authors'] = protoitem['authors']
        item['affiliations'] = dex
        item['date'] = protoitem['date']
        item['publisher'] = protoitem['publisher']
        item['source_url'] = protoitem['source_url']
        item['journal'] = protoitem['journal']
        return item