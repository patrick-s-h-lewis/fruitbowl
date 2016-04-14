'''
.. module:: consume
   :platform: Unix, OSX
   :synopsis: Run a MunchSpider to resolve more metadata from dois with partially 
       resolved metadata from a Crossref Scrape (from  a ShakeSpider or PickSpider)
   
.. moduleauthor:: Patrick Lewis
'''

import json
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.settings import Settings
import Spiders.MunchSpider
import pymongo
from pymongo import MongoClient
from scrapy.utils.log import configure_logging
import scrapingtools
from scrapy.settings import Settings
from fake_mongo import FakeMongo

def get_joblist(file_name):
    '''get the urls to visit during scraping from the dois in the inputted json file
    
    Args:
        file_name (str): name of json list file to extract dois from, each element
            must have key 'doi'. Should be list of json serialised 
            CherryItems.CrossRefItems for correct running of code
   
    Returns:
        doi_links (list): urls to visit for resolving dois in file_name
        doi_sources (dict): keys are dois, values are all additional metadata 
            for the doi found from crossref
    '''
    stub = 'http://dx.doi.org/'
    doi_links=[]
    doi_sources = {}
    with open(file_name) as f:
        j = json.load(f)
        for rec in j:
            doi_link = stub+rec['doi'] 
            doi_links.append(doi_link)
            doi_sources[rec['doi']]=rec
    return (doi_links,doi_sources)
    
def get_domains(dbcoll):
    '''get allowed web domains to constrain the MunchSpider to
    
    Args: dbcoll (object): queriable object (MongoDB cursor or FakeMongo object)
        to get pubisher domains from
    
    Returns:
        domains (list): list of web domains to constrain spider to
    '''
    domains = []
    for rec in dbcoll.find():
        domains.append(rec['pub_website'])
    return domains

def get_publisher_database(settings,mongo=True):
    '''Get a queryable database for the Munchspider to look up publisher xpaths
    
    Args:
        settings (Scrapy Settings object): The current Scrapy settings
        mongo (bool): True if using mongodb, False if using Fake_Mongo interface
    
    Returns:
        publisher_database (object): queriable object (MongoDB cursor or FakeMongo object)
            for getting publisher Xpaths at runtime or getting publisher domain names        
    '''
    if mongo: #use mongodb
        mc=MongoClient(settings.get('PUBS_CONNECTION'))
        publisher_database=mc[settings.get('PUBS_DATABASE')][settings.get('PUBS_COLLECTION')]
    else:# use fake mongo
        publisher_database=FakeMongo('pubs.json')
    return publisher_database

def perform_scrape():
    '''Perform a MunchSpider scrape using the current Scrapy Settings
    '''
	settings = scrapingtools.get_settings()
	publisher_database = get_publisher_database(settings,mongo=False)
	configure_logging({'LOG_FORMAT': '%(levelname)s: %(message)s'})
	(doi_links,doi_sources) = get_joblist(settings.get('COLLECT_FILE_NAME'))
	domains = get_domains(publisher_database)
	runner=CrawlerRunner(settings)
	d=runner.crawl(Spiders.MunchSpider.MunchSpider,
			 start_urls=doi_links,
			 crossref_items = doi_sources,
			 allowed_domains=domains,
			 publisher_database=publisher_database,
			 )
	d2=d.addBoth(lambda _: reactor.stop())
	d2.addCallback(lambda _: scrapingtools.finalise_file(settings.get('COMPLETE_FILE_NAME')))
	d2.addCallback(lambda _: scrapingtools.finalise_file(settings.get('ERROR_FILE_NAME')))

if __name__ == "__main__":#do not perform if importing module
    perform_scrape()