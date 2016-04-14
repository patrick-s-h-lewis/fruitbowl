'''
.. module:: intialise
   :platform: Unix, OSX
   :synopsis: Set up a scraping run
.. moduleauthor:: Patrick Lewis
'''
from scrapy.settings import Settings
from datetime import datetime 
import os
import pickle
import sys
import scrapingtools
import Pipelines.CherryPipelines

def initialise_run(source_file_name):
    '''Set a scraping run by creating settings, files and configuring options
    
    Args:
        source_file_name (str):The source urls or dois to scrape with to resolve dois to metadata
    
    Create a Scrapy settings object to be referred to in all scraping
    Create a directory based on the current date and time to place results in
    Pickle the settings object so it can be maintained if scraping fails or must pause
    '''
	#define default configs:
	err_file_stub = 'errors.json'
	collect_file_stub = 'dois.json'
	complete_file_stub = 'complete.json'
	report_file_stub = 'report.txt'
	stats_file_stub = 'scrapy_stats.txt'
	connection = 'mongodb://localhost:6666/' #ssh pipe
	#connection = 'mongodb://localhost:27017/' #local
	pubs_database = 'Cherry'
	pubs_collection = 'CherryMunch'
	fileconvention = '%H-%M-%S %d-%m-%y'
	now = datetime.now().strftime(fileconvention)
    #create and populate the scrapy settings with desired settings
	settings=Settings()
	subdir = now
	settings.set('SUB_DIRECTORY',subdir)
	settings.set('COLLECT_FILE_NAME',subdir+'/'+collect_file_stub)
	settings.set('ERROR_FILE_NAME',subdir+'/'+err_file_stub)
	settings.set('SOURCE_FILE_NAME',source_file_name)
	settings.set('REPORT_FILE_NAME',subdir+'/'+report_file_stub)
	settings.set('COMPLETE_FILE_NAME',subdir+'/'+complete_file_stub)
	settings.set('SCRAPY_STATS_FILE_NAME',subdir+'/'+stats_file_stub)
	settings.set('PUBS_CONNECTION',connection)
	settings.set('PUBS_DATABASE',pubs_database)
	settings.set('PUBS_COLLECTION',pubs_collection)
	settings.set('ITEM_PIPELINES', {
		'Pipelines.CherryPipelines.CherryPipeline': 100
	})
	settings.set('RETRY_ENABLED',True)
	settings.set('RETRY_TIMES',2)
    
    #make the directory where results will be placed
	os.mkdir(settings.get('SUB_DIRECTORY'))
	scrapingtools.initialise_file(settings.get('COLLECT_FILE_NAME'))
	scrapingtools.initialise_file(settings.get('ERROR_FILE_NAME'))
	scrapingtools.initialise_file(settings.get('COMPLETE_FILE_NAME'))
	#create files where some reporting results will be placed
	with open(settings.get('REPORT_FILE_NAME'),'wb+') as f:
		f.write('')
	with open(settings.get('SCRAPY_STATS_FILE_NAME'),'wb+') as f:
		f.write('')
    #pickle the settings object so it can be retrieved between python sessions
	with open('settings.txt','w') as f:
		pickle.dump(settings,f) 

	print('initialised')

if __name__ == "__main__": #dont run if imported, only if explicitly run
    if len(sys.argv)>1:#if source file name specified
		source_file_name = sys.argv[1]
	else:#revert to default source file name 'in.json'
		source_file_name = 'in.json'
    initialise_run()#set up the scraping run