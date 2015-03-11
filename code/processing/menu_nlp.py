from pymongo import MongoClient, errors
from string import punctuation
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF
from nltk.corpus import stopwords
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

REGEX = re.compile('[^a-zA-Z]')

def clean_doc(doc):
        """
        Pre-process a document before tf-idf. Removes punctuation, stopwords and numbers.
        INPUT: text document.
        """
        doc_clean = REGEX.sub(' ', doc.lower())   
        tokens = doc_clean.split()
        return ' '.join([word for word in tokens if word not in STOPWORDS])

class ExtractFoodTopics(object):
    """
    Extract topics from the corpus of menus.
    """
    def __init__(self, n_topics, n_features):
        """
        INPUT: n_topics, INT, number of food topics used for NMF.
               n_features, INT, number of features used for TF-IDF.
        """
        self.n_topics = n_topics
        self.n_features = n_features
    
    def fit_transform(self, corpus):
        """
        Fit the model to the corpus of menus. Clean the text, TF-IDF, NMF.

        INPUT: Corpus of menus.
        """
        t0 = time()
        print 'Cleaning the menu text...'
        clean_docs = [clean_doc(doc) for doc in corpus]
        self.vect = TfidfVectorizer(ngram_range=(1,3), max_features=self.n_features, max_df=.5)
        print 'Building the vectorizer...'
        self.tfidf = self.vect.fit_transform(clean_docs)
        print 'Done in %.3fs' % (time() - t0)
        self.words = self.vect.get_feature_names()    
        self.__basic_nmf()

    def __basic_nmf(self):
        """
        Performs NMF on the TF-IDF feature matrix from menus to create a topic model.

        INPUT: 2d numpy array - X (size = n_docs*n_tf_idf_features)
        OUTPUT: 2d numpy array - W (Article-Topic weights)
                2d numpy array - H (Topic-Term weights)
        """
        t0 = time()
        print 'NMF factorization...'
        self.nmf = NMF(n_components=self.n_topics)
        self.W = self.nmf.fit_transform(self.tfidf)
        self.H = self.nmf.components_
        print 'Done in %.3fs' % (time() - t0)

    def export_topic_words(self, n_top_words=50):
        """
        Write to file the top words for each topic. Used for assigning topic themes.
        
        INPUT: words from the vectorizer, matrix H with topic-term weights, 
                number of top words
        OUTPUT: write to file - most important terms for each topic, with weights
        """
        for topic_idx, topic in enumerate(self.H):
            top_words = sorted(zip(self.words, topic), key=lambda x: x[1])[:-n_top_words:-1]
            with open('../app/static/topics/food_topic%d.csv' % topic_idx, 'w') as f:
                f.write('text,size,topic\n')
                for word in top_words: 
                    f.write('%s,%s,%s\n' % (word[0], word[1], topic_idx))
       
def create_menu_corpus(filename, menu_text=False, section_text=False, description_text=True):
    """
    Extracts menu data from the foursquare mongoDB to create a corpus.
    INPUT: filename: name of the file used to pickle the corpus
            menu_text (default False) include menu headers in the document
            section_text (default False) include section headers in the document
            description_text (default True) include food descriptions in the document.
    OUTPUT: Menu corpus. Each document is a concatenation of all the words on the menu.
    """
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

def build_menu_topics(n_topics=50, n_features=2500, n_top_words=50, update_corpus=False):
    """
    Loads the corpus data and builds the model.
    INPUT: n_topics INT, number of food topics in the NMF model
           n_features INT, used for TF-IDF
           n_top_words
    OUTPUT: pickled model
    """
    corpus_pkl_file = '../pickles/menu_corpus.pkl'
    food_topics_file = '../pickles/food_topics.pkl'

    if not os.path.isfile(corpus_pkl_file) or update_corpus:
        create_menu_corpus(corpus_pkl_file)
    
    with open(corpus_pkl_file) as f:
        corpus = pkl.load(f)
    
    food_topics = ExtractFoodTopics(n_topics=n_topics, n_features=n_features)
    food_topics.fit_transform(corpus)
    food_topics.export_topic_words(n_top_words=n_top_words)

    with open(food_topics_file, 'w') as f:
        pkl.dump(food_topics, f)

if __name__ == '__main__':
    build_menu_topics(update_corpus=True)
    
    
    
    
    

