from pymongo import MongoClient
from pymongo import errors
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
import cPickle as pkl
import os.path
import numpy as np

def create_menu_corpus(filename):
    '''
    Extracts menu data from the foursquare mongoDB to create a corpus.
    Each document is a concatenation of all the words on the menu.
    '''
    mongoclient = MongoClient()
    coll = mongoclient.foursquare.venues

    
    r = coll.find({'$and': [{'menus.count': {'$gt':0}}, {'menus':{'$exists':'true'}}]}, 
        {'name':1, 'menus':1, '_id':0})
    corpus = []
    
    for doc in r:
        text = []
        for menu in doc['menus']['items']:
            text.append(menu['name'].encode('ascii', 'ignore'))
            text.append(menu.get('description',''))
            for section in menu['entries']['items']:
                text.append(section['name'].encode('ascii', 'ignore'))
                for entry in section['entries']['items']:
                    text.append(entry['name'].encode('ascii', 'ignore'))
                    text.append(entry.get('description', '').encode('ascii', 'ignore'))     
        print doc['name']
        corpus.append(' '.join(text))
    with open(filename, 'w') as f:
        pkl.dump(corpus, f)

def get_top_values(lst, n, labels):
    '''
    INPUT: LIST, INTEGER, LIST
    OUTPUT: LIST

    Given a list of values, find the indices with the highest n values.
    Return the labels for each of these indices.

    e.g.
    lst = [7, 3, 2, 4, 1]
    n = 2
    labels = ["cat", "dog", "mouse", "pig", "rabbit"]
    output: ["cat", "pig"]
    '''
    return [labels[i] for i in np.argsort(lst)[-1:-n-1:-1]]

def basic_nmf(X, n_topics=20):
    '''
    Performs NMF on the TF-IDF feature matrix from menus to create a topic model.

    INPUT: 2d numpy array - X (size = n_docs*n_tf_idf_features)
    OUTPUT: 2d numpy array - W (Article-Topic weights)
            2d numpy array - H (Topic-Term weights)
    '''
    nmf = NMF(n_components=n_topics)
    W = nmf.fit_transform(X)
    H = nmf.components_
    return W, H

def topic_words(words, H, n_top_words=20):
    '''
    INPUT: words from the vectorizer, H topic-term weights, number of top words
    OUTPUT: dict - most important terms for each topic, with the weights
            use this for word clouds
    '''
    topics_dicts = []
    n_topics = H.shape[0]
    for i in xrange(n_topics):
        k, v = zip(*sorted(zip(words, H[i]),
                           key=lambda x: x[1])[:-n_top_words:-1])
        val_arr = np.array(v)
        norms = val_arr / np.sum(val_arr)
        topics_dicts.append(dict(zip(k, norms * 100)))
    return topics_dicts
    

if __name__ == '__main__':
    corpus_pkl_file = '../pickles/menu_corpus.pkl'
    vect_pkl_file = '../pickles/vect.pkl'
    H_pkl_file = '../pickles/H.pkl'

    if not os.path.isfile(corpus_pkl_file):
        create_menu_corpus(corpus_pkl_file)
    with open(corpus_pkl_file) as f:
        corpus = pkl.load(f)

    n_topics = 75
    n_features = 10000
    vect = TfidfVectorizer(stop_words='english', ngram_range=(1,3), 
        max_df=0.4, max_features=n_features)
    print 'building the vectorizer...'
    tfidf = vect.fit_transform(corpus)
    feature_words = vect.get_feature_names()    
    W, H = basic_nmf(tfidf, n_topics=n_topics)

    with open(vect_pkl_file, 'w') as f:
        pkl.dump(vect, f)

    with open(H_pkl_file, 'w') as f:
        pkl.dump(H, f)

    topic_words = topic_words(feature_words, H, n_top_words=10)
    print topic_words
        #vectors = vectorizer.fit_transform(corpus).toarray()
    #words = vectorizer.get_feature_names()


