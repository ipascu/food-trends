from pymongo import MongoClient
from string import punctuation
from pymongo import errors
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from time import time
import cPickle as pkl
import os.path
import numpy as np
import re

ADDITIONAL_STOPWORDS = ['sample', 'menu', 'available', 'popular', 'served', 'contains', 'like', 
    'items', 'plus', 'participating', 'restaurant', 'restaurants', 'good', 'delicious',
    'tasty', 'variety', 'perfect', 'please', 'special', 'check', 'ingredients',
    'hours']
STOPWORDS = set(stopwords.words('english') + ADDITIONAL_STOPWORDS)

class ExtractFoodTopics(object):
    """
    Extract topics from the corpus of menus.
    Use the same transformation and topics to analyze reviews.
    """
    def __init__(self, n_topics=50, n_features=5000):
        self.n_topics = n_topics
        self.n_features = n_features
        self.regex = re.compile('[^a-zA-Z]')

    def __clean_doc(self, doc):
        '''
        Cleans a menu of punctuation, stopwords and numbers.
        '''
        #doc = doc.translate(None, punctuation).lower()
        doc_clean = self.regex.sub(' ', doc.lower())       # remove any non-alphabetic characters
        tokens = doc_clean.split()
        return ' '.join([word for word in tokens if word not in STOPWORDS])  # remove stopwords

    def fit_transform(self, corpus):
        '''
        Fit the topic model to the corpus of menus
        '''
        t0 = time()
        print 'Cleaning the menu text...'
        clean_docs = [self.__clean_doc(doc) for doc in corpus]
        self.vect = TfidfVectorizer(ngram_range=(1,3), max_features=self.n_features, max_df=.5)
        print 'Building the vectorizer...'
        self.tfidf = self.vect.fit_transform(clean_docs)
        print 'Done in %.3fs' % (time() - t0)
        self.words = self.vect.get_feature_names()    
        self.__basic_nmf()

    def find_similarity(self, reviews):
        ''' 
        Given a list of reviews, find the similarity to the food topics.
        '''
        clean_reviews = [self.__clean_doc(review) for review in reviews]
        tfidf = self.vect.transform(clean_reviews)
        review_topics = self.nmf.transform(tfidf)
        #np.dot(self.tfidf.toarray(), self.H.T)
        return review_topics

    def __basic_nmf(self):
        '''
        Performs NMF on the TF-IDF feature matrix from menus to create a topic model.

        INPUT: 2d numpy array - X (size = n_docs*n_tf_idf_features)
        OUTPUT: 2d numpy array - W (Article-Topic weights)
                2d numpy array - H (Topic-Term weights)
        '''
        t0 = time()
        print 'NMF factorization...'
        self.nmf = NMF(n_components=self.n_topics)
        self.W = self.nmf.fit_transform(self.tfidf)
        self.H = self.nmf.components_
        print 'Done in %.3fs' % (time() - t0)

    def topic_words(self, n_top_words=50):
        '''
        INPUT: words from the vectorizer, H topic-term weights, number of top words
        OUTPUT: print - most important terms for each topic, with the weights
                use this for word clouds
        '''
        for topic_idx, topic in enumerate(self.H):
            top_words = sorted(zip(self.words, topic), key=lambda x: x[1])[:-n_top_words:-1]
            with open('../app/static/topics/food_topic%d.csv' % topic_idx, 'w') as f:
                f.write('text,size,topic\n')
                for word in top_words: 
                    f.write('%s,%s,%s\n' % (word[0], word[1], topic_idx))

        # topic_dicts = []
        # for i in xrange(self.n_topics):
        #     k, v = zip(*sorted(zip(self.words, self.H[i]),
        #                        key=lambda x: x[1])[:-n_top_words:-1])
        #     val_arr = np.array(v)
        #     norms = val_arr / np.sum(val_arr)
        #     topic_dicts.append(dict(zip(k, norms * 100)))
        
        # for k in xrange(self.n_topics):
            
            

def create_menu_corpus(filename, menu_text=False, section_text=False, description_text=True):
    '''
    Extracts menu data from the foursquare mongoDB to create a corpus.
    Can pass parameters for whether to include the menu header, description, 
    section header in the corpus.
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
            if menu_text:
                text.append(menu['name'].encode('ascii', 'ignore'))
                text.append(menu.get('description',''))
            for section in menu['entries']['items']:
                if section_text:
                    text.append(section['name'].encode('ascii', 'ignore'))
                for entry in section['entries']['items']:
                    text.append(entry['name'].encode('ascii', 'ignore'))
                    if description_text:
                        text.append(entry.get('description', '').encode('ascii', 'ignore'))     
        print doc['name']
        corpus.append(' '.join(text))
    with open(filename, 'w') as f:
        pkl.dump(list(set(corpus)), f)

if __name__ == '__main__':
    corpus_pkl_file = '../pickles/menu_corpus.pkl'
    food_topics_file = '../pickles/food_topics.pkl'
    
    if not os.path.isfile(corpus_pkl_file):
        create_menu_corpus(corpus_pkl_file)
    with open(corpus_pkl_file) as f:
        corpus = pkl.load(f)

    food_topics = ExtractFoodTopics(n_topics=25, n_features=2500)
    food_topics.fit_transform(corpus)
    food_topics.topic_words()

    with open(food_topics_file, 'w') as f:
        pkl.dump(food_topics, f)

    
    

