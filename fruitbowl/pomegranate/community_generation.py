'''
.. module:: community_generation 
   :platform: Unix, OSX
   :synopsis: methods for using gephi to subdivide documents into modularity communities
.. moduleauthor:: Patrick Lewis
'''
import numpy as np
import codecs
import json
import subprocess
import os 
import time
from fruitbowl.apple import gephi_tools
from fruitbowl.apple import analysis_tools
import collections
import csv

def get_vecs(doi_records,required_dois):
    '''get matrix of vectors for some/all records supplied in 'doi_records'
    
    Args:
        doi_records (list): list of meta-data record dictionaries
            Must have vector representations under keyword 'vector'
        required_dois (list): list of dois from doi_records to build 
            matrix of vectors fro
    
    Returns:
        matrix (np.2darray): (d-by-n) matrix of document vectors from dois in required_dois
    '''
    vecs=[]
    for doi,value in doi_records.iteritems():
        if doi in required_dois:
            vecs.append(np.array(value['vector']))
    matrix=np.transpose(np.array(vecs))
    return Matrix 
    
def get_communities(csv_file_name,cleanup=True):
    '''imports document communities detailed in csv_file_name.
    Deletes the .gexf file and .csv file if cleanup flag is True.
    The community-finding procedure generates lots of files, 
    so deleting them keeps things tidy.
    
    Args:
        csv_file_name (str): name of csv file to read in
        
    Kwargs:
        cleanup (bool): delete source files if True (defaults to true)
    
    Returns:
        doi_dict (dict): dictionary of {doi (str):community (int)} pairs
    '''
    if cleanup:
        os.remove(csv_file_name.split('.')[0]+'.gexf')#delete the temporary graph file
    doi_dict={}#create the graph
    with codecs.open(csv_file_name) as csvf:
        reader = csv.DictReader(csvf,delimiter=',') 
        for row in reader:
            doi_dict[row['label']]=int(row['modularity_class']) #populate dictionary
    if cleanup:
        os.remove(csv_file_name) #delete temporary csv_file
    return doi_dict

def get_modularity(
        dois,
        mat,
        gexf_filename,
        outfilename,
        thresh=0.35,
        subfile='fruitbowl/pomegranate'
        ):
    '''Partition a set of dois into modularity Communities by interfacing with
    java gephi api
    
    Args:
        dois (list): dois to partition
        mat (np.2darray): (n-by-n) matrix of the document cosine similarity weights
        gexf_filename (str): filename stub of the gexf file to create 
        outfilename (str): filename of the csv file to create
    
    Kwargs:
        thresh (int): minium weight of similarity in matrix to draw edges between documents
            (default=0.35)
        subfile (str): directory to write temporary files to
            (default is 'fruitbowl/pomegranate', assuming file structure hasn't been changed)
    
    Returns:
        doi_dict (dict): dictionary of {doi (str):community (int)} pairs
    '''
    #create gephi graph file to open with gephi api
    gephi_tools.gexf_gephi_exporter(
        dois,
        mat,filename=subfile+'/'+gexf_filename,
        user_called=False
        )
    #run gephi api java program to generate modularity communities
    stub = 'mvn exec:java -Dexec.mainClass="org.gephi.toolkit.demos.Main" -Dexec.args="'+gexf_filename+' '+ outfilename+'"'
    process = subprocess.Popen(stub,shell=True,cwd=subfile)
    #wait for process to finish and dump results in csv file
    while True:
        if os.path.isfile(subfile+'/'+outfilename):
            break
        time.sleep(5)
    #read the csv file and load the community partitions
    doi_dict= get_communities(subfile+'/'+outfilename)
    return doi_dict

def generate_communities(mat,sample,max_no_communities=100,min_community_pop=10,max_community_pop=100):
    '''Divide set of documents into modularity communities.
    
    Args:
        mat (numpy.2darray): Cosine similarity matrix for records in sample
        sample (list): list of records
        
    Kwargs:
        max_no_communities (int): target number of communities to divide into (default 100)
        min_community_pop (int): lower bound target for community populations to divide into (default 10)
        max_community_pop (int): upper bound target for community populations to divide into (default 100)
        
    Return:
        communtities_expo (dict): community index keys with lists of dois 
        paths (list): lists of tree paths indices down recursion tree to final communities
    '''
    #create first partition
    print('Creating Communities for '+str(len(sample))+' documents')
    dois_old=[]
    dois = sample.keys()
    dd=get_modularity(dois,mat,'0_cluster.gexf','0_cluster.csv')
    #assign communities found in first partition
    classes = collections.Counter(dd.values())
    for doi,com in dd.iteritems():
        sample[doi]['communities']=[com] 
    comm_no=len(classes.keys())
    
    #define community classifiers
    successful_communities=[k for k,v in classes.items() if min_community_pop<=v<=max_community_pop]#communities in the right population range
    orphaned_communities=[k for k,v in classes.items() if min_community_pop>v]#communities that are smaller than minium target
    super_communities=[k for k,v in classes.items() if max_community_pop<v] #communities bigger than target
    irreducible_communities=[]
    
    #subdivide until reaching target community sizes
    while len(super_communities)>0:
        comm=super_communities.pop()
        dois=[k for k,v in sample.iteritems() if comm in v['communities']]
        if set(dois)==set(dois_old):
            print('Irreducible Community Found, Moving on')
            irreducible_communities.append(comm)
            comm=super_communities.pop()
            dois=[k for k,v in sample.iteritems() if comm in v['communities']]
        #get next vectors
        vecs=get_vecs(sample,dois)
        #create next matrix
        mat=analysis_tools.cosine_mat(vecs,vecs)
        print('Reducing community '+str(comm))
        #get next communities
        dd1=get_modularity(dois,mat,str(comm)+'_cluster.gexf',str(comm)+'_cluster.csv')
        for doi,com in dd1.iteritems():
            sample[doi]['communities'].append(com+comm_no)
        #classify next communities
        classes = collections.Counter(dd1.values())
        successful_communities+=[k+comm_no for k,v in classes.items() if min_community_pop<=v<=max_community_pop]
        orphaned_communities+=[k+comm_no for k,v in classes.items() if min_community_pop>v]
        super_communities+=[k+comm_no for k,v in classes.items() if max_community_pop<v]
        comm_no+=len(classes.keys())
        print(str(len(super_communities)) + ' Communities remaining to subdivide')
        dois_old=dois
    
    #create export dictionary and paths
    communities_expo = {k:[] for k in successful_communities+orphaned_communities+super_communities}
    paths = []
    for doi,values in sample.items():
        communities_expo[values['communities'][-1]].append(doi)
        if not (values['communities']) in paths:
            paths.append(values['communities'])    
    return communities_expo,paths 