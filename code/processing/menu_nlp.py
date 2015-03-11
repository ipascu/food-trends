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
    'hours', 'dinner']
STOPWORDS = set(stopwords.words('english') + stopwords.words('spanish') +
    stopwords.words('french') + stopwords.words('italian') + ADDITIONAL_STOPWORDS)

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
        self.vect = TfidfVectorizer(ngram_range=(1,3), max_features=self.n_features, max_df=.2)
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

def export_topic_words(vect, H, output='/output/food_topic', n_top_words=50):
    """
    Write to file the top words for each topic. Used for assigning topic themes.
    
    INPUT: words from the vectorizer, matrix H with topic-term weights, 
            number of top words
    OUTPUT: write to file - most important terms for each topic, with weights
    """
    for topic_idx, topic in enumerate(H):
        top_words = sorted(zip(vect.get_feature_names(), topic), key=lambda x: x[1])[:-n_top_words:-1]
        with open(output+'%d.csv' % topic_idx, 'w') as f:
            f.write('text,size,topic\n')
            for word in top_words: 
                f.write('%s,%s,%s\n' % (word[0], word[1], topic_idx))

def topic_word_dicts(vect, H, n_top_words):
    '''
    Connects top terms to each topic.
    OUTPUT: dict, most important terms for each topic with the corresponding weights.
    '''
    topic_dicts = []
    n_topics = H.shape[0]

    for i in xrange(n_topics):
        topic_dicts.append(dict(sorted(zip(vect.get_feature_names(), H[i]), 
            key=lambda x: x[1])[:-n_top_words:-1]))
    return topic_dicts

def print_topics(vect, H, n_top_words=20):
    '''
    Prints the most important terms from each NMF topic.
    INPUT: list of dicts (word:weight for each topic)
    OUTPUT: None
    '''
    dicts = topic_word_dicts(vect, H, n_top_words)
    for i, topic in enumerate(dicts):
        l = sorted(topic.items(), key=lambda x: x[1])[::-1]
        print 'Topic #%s' % str(i) 
        for item in l:
            print ' ', item[1], ' ', item[0]
        print '\n'

def create_corpus(filename, menu_text=False, section_text=False, 
    description_text=False, update_corpus=False):
    """
    Extracts menu data from the foursquare mongoDB to create a corpus.
    INPUT: filename: name of the file used to pickle the corpus
            menu_text (default False) include menu headers in the document
            section_text (default False) include section headers in the document
            description_text (default False) include food descriptions in the document.
    OUTPUT: Menu corpus. Each document is a concatenation of all the words on the menu.
    """
    if update_corpus or not os.path.isfile(filename):
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
    else:
        with open(filename) as f:
            corpus = pkl.load(f)
    return corpus
    

def build_menu_topics(fname, mname, n_topics=50, n_features=2500, n_top_words=50, 
                        update_corpus=False):
    """
    Loads the corpus data and builds the model.
    INPUT: n_topics INT, number of food topics in the NMF model
           n_features INT, used for TF-IDF
           n_top_words
           update_corpus True/False flag if you want to overwrite
           fname food topics output file
           mname menu corpus output file
    OUTPUT: pickled model
    """
    corpus = create_corpus(mname, update_corpus=update_corpus)

    food_topics = ExtractFoodTopics(n_topics=n_topics, n_features=n_features)
    food_topics.fit_transform(corpus)
    
    with open(fname, 'w') as f:
        pkl.dump(food_topics, f)

if __name__ == '__main__':
    build_menu_topics(update_corpus=False)
    
    
    
    
    

