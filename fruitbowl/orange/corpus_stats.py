'''
.. module:: corpus_stats
   :platform: Unix, OSX
   :synopsis: functions for generating statistics on document collections

.. moduleauthor:: Patrick Lewis


'''
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np

def plot_zipfian(log_freqs,file_name):
    ''' Plot a Zipfian plot and straight line of best fit and zipfian data
    
    Args:
        log_freqs (list): base 10 log of frequency of words in a text corpus
            in decending order
        file_name (str): name of the png file to save the plot to
    '''
    log_ranks = [math.log(x,10) for x in range(1,len(log_freqs)+1)]#generate x axis
    sample = [] #create an evenly spaced interpolated sample to fit to 
    for s in np.arange(log_ranks[0],log_ranks[-1],log_ranks[1]): 
        sample.append(log_ranks.index(min(log_ranks,key=lambda x:abs(x-s))))
    #perform fitting
    z_grad,z_c = np.polyfit([log_ranks[s] for s in sample],[log_freqs[s]for s in sample],1)
    line_freq = map(lambda x: z_grad*x+z_c,log_ranks)
    #plot the graph
    plt.close()
    plt.plot(log_ranks,log_freqs,'r')
    plt.plot(log_ranks,line_freq,'b')
    plt.xlabel('log(Word Rank)')
    plt.ylabel('log(Word Frequency)')
    plt.savefig(file_name)
    print('Saved Ziphian Plot')
    plt.close()
    
def plot_doc_length_distro(lens,freqs, file_name):
    '''Plot the distibution of document lengths in a corpus
     
    Args:
        lens (list): list of document word lengths
        freqs (list): list of corresponding frequencies of the document word lengths in the corpus
        file_name (str): name of the png file to save the plot to
    '''
    plt.plot(lens,freqs,'o')
    xs=np.linspace(min(lens),max(lens),1000)
    ys=map(lambda x:doc_len_distro(x),xs)
    plt.plot(xs,ys,'r')
    plt.xlabel('Document Word Count')
    plt.ylabel('Frequency')
    plt.savefig(file_name)
    plt.close()
    print('Saved Document Length Distribution Plot')

def doc_len_distro(x):
    '''generate a predicted number of documents with a given word count
    
    Args:
        x (int): document word count
    
    Returns:
        y (int): predicted number of documents in corpus with x words
        
    It was determined the document distribution of Delta6 followed a boltzman
    distribution of the functional form:
        5.991524457330881*x**2*math.exp(-0.00034375*x**2)
    '''
    y= 5.991524457330881*x**2*math.exp(-0.00034375*x**2)
    return y

def get_corpus_stats(doc_iter,outfile_name):
    '''get statistics about a collection of documents
    
    Args:
        doc_iter (docIterator) : an iterator that streams the corpus documents
        outfile_name (str): filename to save plots as
    
    Returns:
        statistics (dict): dictionary with generated corpus statistics 
        
    This function produces two plots, a zipfian plot and document word count distribution
    The function also produces a csv file of ziphian data
    The function also produces a csv file of document word count data
    The function also produces a text document with a statistics summary
    '''
    #counting statistics
    doc_iter.iter_type='SIMPLE'
    word_freq = Counter()
    word_count = 0
    document_count = 0
    unique_word_count=0
    document_lengths = Counter()
    for doc in doc_iter:
        word_count+=len(doc)
        document_count+=1
        document_lengths.update([len(doc)])
        upd = []
        word_freq.update(doc)
    unique_word_count=len(word_freq)
    mean_doc_length = float(word_count)/float(document_count)
    mode_doc_length = document_lengths.most_common(1)[0]
    print('Generated Counting Stats')
    
    #generating and plotting zipfian statistics 
    ranked_word_freq = word_freq.most_common()
    zipfian_table = []
    for rank in range(unique_word_count):
        w = ranked_word_freq[rank][0]
        f = ranked_word_freq[rank][1]
        log_r = math.log(rank+1,10)
        log_f = math.log(f,10)
        zipfian_table.append((w,r,log_r,f,log_f))
    print('Generated Ziphian Data')
    log_freqs = list(zip(*zt)[4])
    plot_zipfian(log_freqs,outfile+'_zipfian_plot.png')
    #plotting document lengths
    doc_lens = counter.keys()
    doc_len_freqs=counter.values()
    plot_doc_lenth_distro(doc_lens,doc_len_freqs,outfile_name+'_document_word_lengths.png')
    #write zipfian data to disk
    with open(outfile_name+'_zipfian_data.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['word','rank','log rank','freqency','log_frequncy'])
        writer.writerows(zipfian_table)
    print('Writen Ziphian Data To file')
    #write document data to disk
    with open(outfile_name+'_document_lengths.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['words per document','number of documents'])
        writer.writerows(zip(document_lengths.keys(),document_lengths.values()))
    print('Writen Document Length Distribution data to file')
    #write statistics summary to disk
    with open(outfile_name+'stats.txt','wb') as f:
        f.write('Word count : '+str(word_count)+'\n')
        f.write('Unique words : ' + str(unique_word_count)+'\n')
        f.write('Mean document word count : ' + str(mean_doc_length)+'\n')
        f.write('Mode document word count : '+ str(mode_doc_length[0])+'\n')
        f.write('Document count : ' + str(document_count)+'\n')
        f.write('Ziphian gradient : '+str(z_grad)+'\n')
        f.write('Ziphian intercept : '+str(z_c)+'\n')
        f.write('most_frequent 10 words : '+'\n')
        for w in zipfian_table[0:10]:
            f.write('"'+w[0]+'" : '+str(w[3])+' occurances\n')
    print('Written stats report to file')
    #create statistics summary dictionary to return
    statistics={'word_count':word_count,
        'unique_word_count':unique_word_count,
        'document_count':document_count,
        'mean_doc_length':mean_doc_length,
        'mode_doc_length':mode_doc_length[0],
        '10_most_common_words':list(zip(*zipfian_table[:10])[0])}
    return statistics
        
        
        
    
