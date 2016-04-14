'''
.. module:: analyse
   :platform: Unix, OSX
   :synopsis: Module for analysing scraping runs and producing reports

.. moduleauthor:: Patrick Lewis
'''
import json
import re
import datetime
import scrapingtools

def perform_analysis():	
    '''Produce scraping report after scraping run
    
    Loads the current settings and analyses collected data in the error datastore
    and complete records datastore. Creates a file with name specified in the settings
    object as 'REPORT_FILE_NAME'.
    '''
    #get data sources
	settings = scrapingtools.get_settings()
	err_file_name=settings.get('ERROR_FILE_NAME')
	complete_file_name=settings.get('COMPLETE_FILE_NAME')
	report_file_name=settings.get('REPORT_FILE_NAME')
    #perform analysis
	with open(complete_file_name,'r') as sr: #load collected results into categories and count
		with open(err_file_name,'r') as fr: #load errors into categories and count
			s = json.load(sr)
			f = json.load(fr)
			doi_l=[]
			coll_l=[]
			pub_time_l=[]
			source_time_l=[]
			miss_l=[]
			pub_l=[]
			doi_no=0
			coll_no=0
			pub_time_no=0
			source_time_no=0
			miss_no=0
			for rec in f:
				if rec['error'].keys()==['collection']:#collection errors
					coll_no+=1
					coll_l.append(rec)
				if rec['error'].keys()==['404']:#404 errors
					if rec['error']['404']=='source':#404 errors for source website
						source_time_no+=1
						source_time_l.append(rec)
					else:#404 errors for publisher websites
						pub_time_no+=1
						pub_time_l.append(rec)
				if rec['error'].keys()==['broken_doi']:#errors due to broken dois
					doi_no+=1
					doi_l.append(rec)
				if rec['error'].keys()==['missing_pub']:#errors due to missing publisher xpaths
					miss_no+=1
					miss_l.append(rec)
			for rec in s:
				pub_l.append(rec['publisher'])#collect the publisher names correctly captured
	#calculate metrics based off collections
	success_no=len(s)#number of successfully resolved dois
	fail_no=len(f)#number of lost records
	parse_no = success_no+fail_no#number parsed
	conv_no = float(success_no)/float(parse_no)#fractional yield
	coll_pub = [r['error']['collection'] for r in coll_l]#publishers involved in conversion errors
	miss_pub = [r['error']['missing_pub'] for r in miss_l]#publishers missed by program due to missing xpaths
	#get maxes
	if len(coll_pub)>0: 
		most_coll_errors = max(set(coll_pub), key=coll_pub.count) 
	else:
		most_coll_errors = 'No Collection Errors'
	if len(miss_pub)>0:
		most_missing_errors = max(set(miss_pub), key=miss_pub.count)
	else:
		most_missing_errors = 'No Missing Publisher Errors'
	if len(pub_l)>0:
		most_pub = max(set(pub_l), key=pub_l.count)
	else: 
		most_pub = 'No Most Frequent Publisher'
	
	#write error report with results of metrics
	with open(report_file_name,'ab+') as f:
		f.write('*'*70+'\n')
		f.write("Analysis of scraping run performed at "+datetime.datetime.now().strftime('%H:%m %d %B %Y')+'\n')
		f.write('*'*70+'\n'+'\n')
		f.write('Total records parsed:                             '+ str(parse_no)+'\n')
		f.write('Total records successfully collected:             ' + str(success_no)+'\n')
		f.write('Conversion rate:                                  '+'%.4f'%(conv_no*100)+'%'+'\n')
		f.write('\n'+'\n')
		f.write('-'*70+'\n')
		f.write('Losses Breakdown:'+'\n')
		f.write('-'*70+'\n'+'\n')
		f.write('Total No. of records not converted:               '+ str(fail_no)+'\n')
		f.write('No. lost due to errors in collection:             '+ str(coll_no)+'\n')
		f.write('No. lost due to timeouts to sources websites:     '+ str(source_time_no)+'\n')
		f.write('No. lost due to timeouts to publishers:           '+ str(pub_time_no)+'\n')
		f.write('No. lost due to broken dois:                      '+ str(doi_no)+'\n')
		f.write('No. lost due to missing publisher info:           '+str(miss_no)+'\n')
		f.write('\n'+'\n')
		f.write('-'*70+'\n')
		f.write('Collection Errors Breakdown:'+'\n')
		f.write('-'*70+'\n'+'\n')
		f.write('Most collection errors for publisher:           '+most_coll_errors+'\n')
		f.write('\n'+'\n')
		f.write('Publisher                                   no. of errors')
		f.write('\n')
		for i in set(coll_pub):
			pad = len(i)
			f.write(i+' '*(50-pad)+str(coll_pub.count(i)) +'\n')
		f.write('\n'+'\n')
		f.write('-'*70+'\n')
		f.write('Missing publisher Errors Breakdown:'+'\n')
		f.write('-'*70+'\n'+'\n')
		f.write('Most frequent missing publisher:                '+most_missing_errors+'\n')
		f.write('\n'+'\n')
		f.write('Publisher                                number of records')
		f.write('\n')
		for i in set(miss_pub):
			pad = len(i)
			f.write(i+' '*(50-pad)+str(miss_pub.count(i)) +'\n')
		f.write('-'*70+'\n')
		f.write('Scraped Publisher Breakdown:'+'\n')
		f.write('-'*70+'\n'+'\n')
		f.write('Most frequent publisher:                        '+most_pub+'\n')
		f.write('\n'+'\n')
		f.write('Publisher                                number of records')
		f.write('\n')
		for i in set(pub_l):
			pad = len(i)
			f.write(i+' '*(50-pad)+str(pub_l.count(i)) +'\n')
		f.write('\n'+'*'*70)
	print('Scraping Run Analysed.')

if __name__ == "__main__":#do not execute on import
	perform_analysis()