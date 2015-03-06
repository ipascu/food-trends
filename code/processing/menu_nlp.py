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

if __name__ == '__main__':
    filename = '../pickles/menu_corpus.pkl'
    if not os.path.isfile(filename):
        create_menu_corpus(filename)

    with open(filename) as f:
        corpus = pkl.load(f)

    n_topics = 75
    n_features = 7500
    vect = TfidfVectorizer(stop_words='english', ngram_range=(1,3), 
        max_df=0.4, max_features=n_features)
    nmf = NMF(n_components=n_topics)

    tfidf = vect.fit_transform(corpus)
    W = nmf.fit_transform(tfidf)
    H = nmf.components_

    feature_words = vect.get_feature_names()

    with open('output.txt', 'w') as f:
        for i in xrange(H.shape[0]):
            f.write('\nTopic %d' %i)
            f.write('%s' % [feature_words[j] for j in np.argsort(H[i,:])[:-15:-1]])
        #vectors = vectorizer.fit_transform(corpus).toarray()
    #words = vectorizer.get_feature_names()


