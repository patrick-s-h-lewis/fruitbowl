'''
.. module:: PickSpider
   :platform: Unix, OSX
   :synopsis: Data processing pipeline to record scrapy items correctly

.. moduleauthor:: Patrick Lewis


'''
import json
from scrapy.exceptions import DropItem
import ScrapingTools
from Items import CherryItems
        
class CherryPipeline(object):
    '''Pipeline for handing scrapy items generated in scraping
    '''
    @classmethod
    def from_crawler(cls,crawler):#get the settings from scrapy
        settings = crawler.settings
        return cls(settings)
        
    def __init__(self,settings):
    '''Make a cherryPipeline
    Args:
        settings (Scrapy Settings): Settings object in use for this scraping run
    '''
        self.collect_file = open(settings.get('COLLECT_FILE_NAME'), 'ab+')
        self.err_file = open(settings.get('ERROR_FILE_NAME'),'ab+')
        self.stats_file_name = settings.get('SCRAPY_STATS_FILE_NAME')
        self.complete_file = open(settings.get('COMPLETE_FILE_NAME'),'ab+')
        self.items_seen = set()

    def process_item(self, item, spider):
        '''Process an item generated in scraping
       
         Args:
             item (CherryItem): item to process
         Returns:
             item (CherryItem): processed item
    '''
        if isinstance(item, CherryItems.BrokenItem): #record in error log
            primary_key='doi'
            write_file = self.err_file
            line = json.dumps(dict(item)) + ",\n"
            write_file.write(line)
            return item
        else:
			if isinstance(item, CherryItems.CrossRefItem):#set the primary key for duplicate filtering
				primary_key='doi'
				write_file=self.collect_file
			if isinstance(item, CherryItems.CompleteItem):
				primary_key='doi'
				write_file=self.complete_file
			if isinstance(item, CherryItems.SeekItem):
				primary_key='url'
				write_file=self.collect_file
			if item[primary_key] in self.items_seen: #duplicate filter
				raise DropItem("Duplicate item found")
			else:
				self.items_seen.add(item[primary_key]) #record item if not duplicate in relevant store
				line = json.dumps(dict(item)) + ",\n"
				write_file.write(line)
				return item
    
    def close_spider(self,spider):
        '''perform actions on termination of spider scraping
        
        Args:
            spider (Scrapy Spider): spider that is closing
        '''
        stats=spider.crawler.stats.get_stats() # get scrapy stats and record
        stats_items=stats.items()
        with open(self.stats_file_name,'a') as f:
            for k,v in stats_items:
                f.write('{"'+str(k)+'":"' + str(v)+"},\n")
        #close the writers
        self.err_file.close()
        self.collect_file.close()
        self.complete_file.close()