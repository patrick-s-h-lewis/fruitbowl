'''
.. module:: model_training 
   :platform: Unix, OSX
   :synopsis: train word2vec and doc2vec models using documentIterator

.. moduleauthor:: Patrick Lewis
'''
import gensim.models.doc2vec as d2v
import gensim.models.word2vec as w2v

def train_doc2vec(doc_iter,epochs=24,save=False,save_name='doc2vec',dimensionality=100):
    '''train a doc2vec model from a set of documents streamed by a doc_iter
    
    Args:
        doc_iterator (orange.doc_iterator.DocumentIter): document iterator for 
            streaming documents into the model sentence by sentece. Needs 
            to be JsonDiskIter or MongoIter
    
    Kwargs:
        epochs (int): number of epochs to train for. Defaults to 24
        save (bool): if True, Save the model to disk when training complete. 
            Defaults to False.
        save_name (str): file name for saving model to, defaults to 'doc2vec'
        dimensionality (int): dimensions of representation vectors to train 
            Defaults to 100.
    
    Returns:
        d2vmodel (gensim.models.doc2vec.Doc2Vec): trained doc2vec model
    '''
    doc_iter.iter_type='LABELED_SENTENCES'
    d2vmodel = d2v.Doc2Vec(
        size=dimensionality,
        window=8,
        min_count=1,
        alpha=0.025,
        min_alpha=0.025
    )
    d2vmodel.build_vocab(doc_iter)
    for epoch in range(epochs):#train!
        print('training epoch: '+str(epoch))
        d2vmodel.train(doc_iter)
        d2vmodel.alpha-=0.001
        d2vmodel.min_alpha=d2vmodel.alpha
    if save: #save the model
        d2vmodel.save(save_name)
    print('Model Trained')
    return d2vmodel
    
def train_word2vec(doc_iter,epochs=24,save=False,save_name='word2vec',sg=1,dimensionality=100):
    '''train a doc2vec model from a set of documents streamed by a doc_iter
    
    Args:
        doc_iterator (orange.doc_iterator.DocumentIter): document iterator for streaming
            the documents to the model sentence by sentence for training.
             
Kwargs:
        epochs (int): number of epochs to train for. Defaults to 24
        save (bool): if True, Save the model to disk when training complete. 
            Defaults to False.
        save_name (str): file name for saving model to, defaults to 'word2vec'
        sg (int): train a skipgram model (1) or a cbow model (0) (defaults to 1)
        dimensionality (int): dimensions of representation vectors to train 
            Defaults to 100.
    '''
    doc_iter.iter_type='SENTENCES'
    model=w2v.Word2Vec(doc_iter,min_count=1,size=dimensionality,sg=sg,iter=epochs)#train!
    if save:#save the model
        model.save(save_name)
    print('Model Trained')
    return model