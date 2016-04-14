'''
.. module:: Cherryitems
   :platform: Unix, OSX
   :synopsis: Scrapy Item classes for use in scraping university and publisher websites
.. moduleauthor:: Patrick Lewis

'''
import scrapy

class CrossRefItem(scrapy.Item):
    '''scrapy item for encapuslating partially complete metadata for an article
    '''
    doi = scrapy.Field()
    title = scrapy.Field()
    authors = scrapy.Field()
    affiliations = scrapy.Field()
    date = scrapy.Field()
    publisher = scrapy.Field()
    journal = scrapy.Field()
    source_url = scrapy.Field()
    crossref_doi = scrapy.Field()
    
class CompleteItem(scrapy.Item):
   '''Scrapy item for encapsulating complete metadata for an article'''
    doi = scrapy.Field()
    title = scrapy.Field()
    abstract = scrapy.Field()
    authors = scrapy.Field()
    affiliations = scrapy.Field()
    date = scrapy.Field()
    journal = scrapy.Field()
    publisher = scrapy.Field()
    source_url = scrapy.Field()
    
class BrokenItem(scrapy.Item):
   '''scrapy item for encapsulating error messages in scraping
   '''
    doi=scrapy.Field()
    source_url=scrapy.Field()
    error=scrapy.Field()
    
class SeekItem(scrapy.Item):
    '''scraping item for encapsulating urls that may contain dois
    '''
    url = scrapy.Field()
    num_dois = scrapy.Field()
    