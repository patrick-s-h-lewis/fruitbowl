'''
.. module:: dim_reduction 
   :platform: Unix, OSX
   :synopsis: reduce dimensions of inputted vectors

.. moduleauthor:: Patrick Lewis
'''
from sklearn.manifold import MDS
from sklearn.decomposition import PCA
from bhtsne.bhtsne import TSNE as BHTSNE

def reduce_dimensions(vecs,tsne=True,dims=2):
    '''reduce dimensions of inputted vectors using TSNE or PCA
    
    Args:
        vecs (list or numpy.2darray):list of n d-dimensional numpy.arrays or d-by-n matrix
            containing the vectors to reduce.
    
    Kwargs:
        tsne (bool): If True, perform BHTSNE reduction, if False, perform PCA reduction
        dims (int): number of dimensions to reduce to (defaults to 2)
        
    Returns:
        reduced_vecs (numpy.2darray); n-by-dims matrix containing reduced vectors
        
    '''
    if tsne:
        transform=BHTSNE(n_components=dims)
        reduced_vecs = transform.fit_transform(vecs)
    else:
        transform=PCA(copy=True, n_components=dims, whiten=False)
        reduced_vecs = transform.fit_transform(vecs)
    return reduced_vecs
    