'''
.. module:: gephi_tools 
   :platform: Unix, OSX
   :synopsis: tools for tranforming and exporting cosine matrices into gephi networks

.. moduleauthor:: Patrick Lewis
'''
import numpy as np

def csv_gephi_exporter(dois,mat,file_name='connect.csv',threshold=0.35):
    '''Create a Gephi-readable network graph csv file
    
    Args:
        dois (list): list of n dois of documents included in network, become node labels.
        mat (numpy.2darray): (n-by-n) cosine matrix for n document nodes
    
    Kwargs:
        file_name (str): name of csv file to create (defaults to 'connect.csv')
        threshold (float): threshold of cosine similarity weight above which to create edges
            between nodes. If too low, graph can become extremely complex. (default 0.35)
    
    If threshold is negative, every node will connect with every other node, with O(n^2)
    scaling, problematic if large number of nodes
    '''
    with open(file_name,'w') as f:
        masked=mat*(mat>threshold)
        f.write(';'+';'.join(dois)+'\n')
        for i in range(mat.shape[0]):
            masked[i,i]=0.
            ex=(';'.join([str(j) for j in masked[i] if j>threshold]))
            ex=dois[i]+';'+ex+'\n'
            f.write(ex)

def gexf_gephi_exporter(dois,mat,filename='connect.gexf',threshold=.35,user_called=True):
    '''Create Gephi gexf network graph file for cosine mat with labels 'dois'
     Args:
        dois (list): list of n dois of documents included in network, become node labels.
        mat (numpy.2darray): (n-by-n) cosine matrix for n document nodes
    
    Kwargs:
        file_name (str): name of gexf file to create (defaults to 'connect.gexf')
        threshold (float): threshold of cosine similarity weight above which to create edges
            between nodes. If too low, graph can become extremely complex. (default 0.35)
        user_called (bool): if True, prints messages to stdout when export complete (default trues)
    
    If threshold is negative, every node will connect with every other node, with O(n^2)
    scaling, problematic if large number of nodes.
    The weights of edges are scaled from 0.35-1 to range 0-1
    '''
    
    node_count=len(dois) #get number of noes to create
    edge_count=(np.sum(mat>threshold)-mat.shape[0])/2 #get number of edges to create
    #build header string
    header='''<?xml version="1.0" encoding="UTF-8"?>
<gexf xmlns:viz="http:///www.gexf.net/1.1draft/viz" version="1.1" xmlns="http://www.gexf.net/1.1draft">
<meta lastmodifieddate="2010-03-03+23:44">
<creator>Gephi 0.7</creator>
</meta>
<graph defaultedgetype="undirected" idtype="string" type="static">
<nodes count="'''
    header=header+str(node_count)+'">'
    #build footer string
    footer='''\n</edges>\n</graph>\n</gexf>'''
    with open(filename,'w') as f:
        f.write(header)#write head
        for i in range(node_count):#write nodes to file
            node='\n<node id="'+str(float(i))+'" label="'+dois[i]+'"/>'
            f.write(node)
        f.write('\n</nodes>\n<edges count="'+str(edge_count)+'">')
        edge_no=0
        for i in range(node_count):#write edges to file
            for j in range(i+1,node_count):
                if mat[i,j]>threshold:
                    ex = (mat[i,j]-threshold)
                    f.write(
                        '\n<edge id="'+
                        str(float(edge_no))+
                        '" source="'+str(float(i))
                        +'" target="'+str(float(j))+
                        '" weight="'+str(ex)+'"/>')
                    edge_no+=1
        f.write(footer)#write the footer
    if user_called:#tell the user the export is finished if run by user
        print('graph exported: '+filename)