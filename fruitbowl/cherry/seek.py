'''
.. module:: seek
   :platform: Unix,Mac OSX
   :synopsis: Scraping framework for finding and identifying dois on webpages
   requires external argument with filename of inputted json file
   json file must be a list of json objects with fields 'url':<url> and 'root':<the domain the scraper is allowed to explore>

.. moduleauthor:: Patrick Lewis 

'''
import sys
import json
from twisted.internet import reactor
import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.settings import Settings
from scrapy.utils.log import configure_logging
import SeekSpider
import scrapingtools

if __name__ == "__main__":
	input_list=sys.argv[1]
	#get list of root websites to explore for dois
	with open(input_list,'r') as f:
		j = json.load(f)
		s_u = [it['url'] for it in j]
		a_d = [it['root'].split('/')[0] for it in j]
	settings = scrapingtools.get_settings()

	#settings.set('LOG_ENABLED',True)
	configure_logging({'LOG_FORMAT': '%(levelname)s: %(message)s'})
    #set up the deferred scraping run:
	runner = CrawlerRunner(settings)
	runner.crawl(
		SeekSpider.SeekSpider,
		start_urls=s_u,
		allowed_domains=a_d,
		)
	d=runner.join()
	#add callbacks for when the run finishes
	d2 = d.addBoth(lambda _:reactor.stop())
	d2.addCallback(lambda _:scrapingtools.finalise_file(outfile))
	reactor.run()
