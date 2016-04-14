'''
.. module:: analysis_tools 
   :platform: Unix, OSX
   :synopsis: Library of tools for use in document vector analysis

.. moduleauthor:: Patrick Lewis
'''
import numpy as np
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE, MDS
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def cosine_mat(a,b):
    '''Create a Cosine matrix from vector matrices a,b
    
    Args:
        a (numpy.2darray): (d-by-n) matrix of  n d-dimensional vectors
        b (numpy.2darray): (d-by-m) matrix of  m d-dimensional vectors
        
    Returns:
       result (numpy.2darray): (m-by-n) cosine matrix
    '''
    dots= np.dot(np.transpose(a),b)
    inter=dots/np.linalg.norm(b,axis=0)
    result=np.transpose(inter)/np.linalg.norm(a,axis=0)
    return result
    
def get_average_vector(a):
    '''Get the mean vector from matrix of document vectors
    
    Args:
        a (numpy.2darray): (d-by-n) matrix of n d-dimensional vectors to 
    Returns:    
        result (numpy.array): d-dimensional vector'''
    result= np.sum(a,axis=1)
    return result

def get_max(sim_mat):
    '''get the highest value in the cosine matrix and its indices
    
    Args:
        sim_mat (numpy.2darray):
    
    Returns:
        value (numpy.float64): highest value in matrix
        a_ind (int): row of highest value
        b_ind (int): column of highest value
    '''
    dim_b,dim_a = sim_mat.shape
    sim_max = np.argmax(sim_mat)
    a_ind=sim_max%dim_a
    b_ind=sim_max/dim_a
    value=sim_mat[b_ind,a_ind]
    return (value,a_ind,b_ind)

def get_maxes(a,b,n_maxes=1):
    '''get the highest similarities between documents in vector matrices a and b
    
    Args:
        a (numpy.2darray): (d-by-n) matrix of  n d-dimensional vectors
        b (numpy.2darray): (d-by-m) matrix of  m d-dimensional vectors
    
    Kwargs:
        n_maxes (int): number of highest similarities to return (defaults to 1)
    
    Returns:
        sim_export (dict): dictionary of dictionaries detailing similarities
        
    returns a dictionary with keys 1...n_maxes (most similar to nth most similar)
    and values:
         {'similaritity':cosine similarity for document pair,
         a_ind : index of document in a-matrix
         b_ind : index of document in b-matrix}
    if a is numerically equal to b, it assumes the documents are the same
    and removes self similarities (the cosine matrix diagonal)
    '''
    total_maxes=n_maxes
    sim_export={}
    sim_mat=cosine_mat(a,b) #calculate the cosine similarity
    if np.array_equal(a,b): #remove self similiarity if a is equal to b
        for i in range(a.shape[1]):
            sim_mat[i,i]=0
    while n_maxes>0:
        n_maxes-=1
        s,a_ind,b_ind=get_max(sim_mat)
        sim_export[total_maxes-n_maxes]={'similarity':s,'a_ind':a_ind,'b_ind':b_ind}
        #set the highest value to zero so for next iteration it isnt highest any more
        sim_mat[b_ind,a_ind]=0.
    return sim_export

def get_vectors(dcit,vector_type='d2v-d',return_recs=True):
    '''Get vectors from an orange.docIterators.DocumentIter and pack them into a matrix
    
    Args:
        dcit (orange.docIterators.DocumentIter) : the DocumentIter to stream documents from
    
    Kwargs:
        vector_type (str): the vector model to use. Default 'd2v-d' (doc2vec document vectors)
        return_recs (bool): returns the entire records from dcit in addition to vectors and dois
    Returns:
        return_mat (numpy.2darray) : The vectors of documents in dcit, packed into matrices
        dois (list) : dois of the documents in the dcit
   
    Optional Return:    
        recs (dict) : all the records in dcit, keys=dois, values=records. 
            only returned if return_recs flag is set toTrue
    
    WARNING - not a memory friendly operation. Do not use if dcit streams a large number
        of documents (dependent on system but >100 000 will probably crash)
    
    The documents streamed by dcit must have precomputed vectors stored in them.
    The document must have a key 'vectors' with a dictionary of vectors in it, 
    containing vector_type kwarg argument as key
    '''
    dcit.iter_type='VECTORS'
    recs={}
    vecs=[]
    dois=[]
    for rec in dcit:
        if return_recs:
            recs[rec['doi']]={'vector':rec['vectors'][vector_type]}
        vecs.append(np.array(rec['vectors'][vector_type]))
        dois.append(rec['doi'])
    return_mat = np.transpose(np.array(vecs))
    if return_recs:
        return return_mat,dois,recs
    else:
        return return_mat,dois

def get_doi_sims(a_vecs,a_dois,b_vecs,b_dois,n_maxes=5):
    '''Wrapper for get_maxes. Returns most similar documents between sets a and b
    
    Args:
        a_vecs (numpy.2darray):(d-by-n) matrix of n d-dimensional vectors
        a_dois (list): dois of documents in a_vecs
        b_vecs (numpy.2darray):(d-by-n) matrix of n d-dimensional vectors
        b_dois (list): dois of documents in b_vecs
        
    Kwargs:
        n_maxes (int): number of highest similarities to return (default 5)
    
    Returns:
        export (dict): dictionary containing highest results.
        
    If a_vecs is a single vector (one document), the function compares this
    pairwise to documents in b_vecs
    if a_vecs is a matrix (collection of documents), the function
    performs comparisons between every doc in a with every doc in b
    The returned dictionary has keys 1...n_maxes, (most similar...nth most similar)
    with values {'a_doi',doi of document in a of similarity pair,
        'b_doi',doi of document in b of similarity pair
        'similarity':cosine similarity
        }
    If a_vecs is a single vector rather than a matrix, the returned dictionary has
    slightly different values: {'doi':doi in b with high similarity to document a
    'similarity':cosine similarity}
    '''
    if len(a_vecs.shape)==1:
        single_flag=True
        a_vecs=a_vecs.reshape(a_vecs.shape[0],1)
    else:
        single_flag=False
    sims=get_maxes(a_vecs,b_vecs,n_maxes=n_maxes)
    export={}
    for ind,entry in sims.items():
        if single_flag:
            export[ind]={
                'doi':b_dois[entry['b_ind']],
                'similarity':entry['similarity']
            }
        else:
            export[ind]={
                'a_doi':a_dois[entry['a_ind']],
                'b_doi':b_dois[entry['b_ind']],
                'similarity':entry['similarity']
            }
    return export

def get_ave_sim(a,b=None):
    '''Get the average cosine similarity score from one or two sets of document vectors
    
    Args:
        a (numpy.2darray):(d-by-n) matrix of n d-dimensional vectors
    
    Kwargs:
        b (numpy.2darray):(d-by-n) matrix of n d-dimensional vectors.
            Defaults to None, in which case self-similarity average of 'a' is computed 
    
    Returns:
        ave (float): average cosine similarity for all pairs betwwen a and b, 
            or average of self-cosine-similarity for a if b not supplied
    '''
    if b is None:#get average of self similarity of a
        sim_mat=cosine_mat(a,a)
        raw_sum=np.sum(sim_mat)-np.sum(sim_mat.diagonal())
        divisor=sim_mat.shape[0]**2-sim_mat.shape[0]
        ave=raw_sum/divisor
    else:#get average of the pairwise similarities between a and b
        sim_mat=cosine_mat(a,b)
        raw_sum = np.sum(sim_mat)
        divisor = sim_mat.shape[0]*sim_mat.shape[1]
        ave=raw_sum/divisor
    return ave

def get_sim(v1,v2):
    '''get cosine similarity between two vectors
    
    Args:
        v1 (numpy.array): d-dimensional vector 
        v2 (numpy.array): d-dimensional vector
    
    Returns:
        sim (float): the value of cosine(theta) between the two vectors
    '''
    sim= np.dot(v1,v2)/(np.linalg.norm(v1)*np.linalg.norm(v1))
    return sim