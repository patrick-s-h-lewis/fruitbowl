'''
.. module:: collect
   :platform: Unix, OSX
   :synopsis: Module for running PickSpider and ShakeSpider 
.. moduleauthor:: Patrick Lewis
'''
import json
from twisted.internet import reactor
import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.settings import Settings
from scrapy.utils.log import configure_logging
import Spiders.PickSpider
import Spiders.ShakeSpider
import Pipelines.CherryPipelines
import scrapingtools
import sys
from datetime import datetime 
import os
import pickle
import scrapingtools

def get_pick_joblist(file_name):
    '''get the list of scraping destinations for PickSpiders to run on from inputted file
    
    Args:
        file_name (str): name of json file of list of inputted websites
    
    Returns:
        start_urls (list): list of url strings to visit
        allowed_domains (list): list of allowed domains to constrain spider to
    '''
    start_urls=[]
    allowed_domains=[]
	with open(file_name,'r') as f:
		li=json.load(f)
		for record in li:
			start_urls.append(record['url'])
			allowed_domains.append(record['url'].split('/')[2])
	return (start_urls,allowed_domains)

def get_shake_joblist(file_name):
    '''Get dois and list of source urls for a ShakeSpider to run on from inputted file
    
    Args:
        file_name (str): name of json file of list of inputted dois to run
        
    Returns:
        dois (list): list of inputted dois to scrape on
        doi_sources (list): list of urls the dois in the list of dois originate from
    '''
    dois=[]
    doi_sources=[]
    with open(file_name,'r') as f:
            li=json.load(f)
            for record in li:
                dois.append(record['doi'])
                doi_sources.append(record['source_url'])
        return (dois,doi_sources)
    
        
def perform_scrape(pick_or_shake):
    '''Perform a Scraping run for either a PickSpider or Shakespider.
    
    Args:
        pick_or_shake (str): string 'pick' or 'shake' specifiying what spider to run
    '''
    #get the settings and configure the logging level
    settings = scrapingtools.get_settings()
	settings.set('LOG_ENABLED',True)
	configure_logging({'LOG_FORMAT': '%(levelname)s: %(message)s'})
    #get the job list for the spider
	if pick_or_shake=='Pick':
	    joblist=get_pick_joblist(settings.get('SOURCE_FILE_NAME'))
	elif pick_or_shake='Shake':
	    joblist=get_pick_joblist(settings.get('SOURCE_FILE_NAME'))
    else:
        #if wrong input given, assume a pickspider
        joblist=get_pick_joblist(settings.get('SOURCE_FILE_NAME'))
        
    #create a deferred runner
	runner = CrawlerRunner(settings)
    #add the relevant spider crawl to the deferred runner
	if pick_or_shake=='pick':
		d=runner.crawl(Spiders.PickSpider.PickSpider,start_urls=joblist[0],allowed_domains=joblist[1])
	elif pick_or_shake=='shake':
		d=runner.crawl(Spiders.ShakeSpider.ShakeSpider,dois=joblist[0],doi_sources=joblist[1])
	#add callbacks to stop the runner and finalise legal file
	d2 = d.addBoth(lambda _:reactor.stop())
	d2.addCallback(lambda _:scrapingtools.finalise_file(
		settings.get('COLLECT_FILE_NAME'))
		)
	#run the scrape
	reactor.run()
    
if __name__ == "__main__":#dont run if module imported
	pick_or_shake = sys.argv[1]
	perform_scrape(pick_or_shake)