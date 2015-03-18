import pandas as pd
import numpy as np
import cPickle as pkl
from sklearn.feature_extraction.text import CountVectorizer
from gensim.models import Word2Vec
import time

WORD2VEC_MODEL = '../data/word2vec_modelf'
START_DATE = '2014-12-01'
END_DATE = '2015-03-31'
REVIEWS = '../data/reviews%s%s.json' % (START_DATE, END_DATE)


class ReviewModel(object):
    """Model used for map plots using word counts and word2vec queries."""
    def __init__(self, model_file, similarity=.65):
        """
        Args:
            model_file: filepath for the trained word2vec model
            similarity: cutoff for similarity measure for queries
        """
        self.model = Word2Vec.load(model_file)
        self.topic = {}
        self.similarity = similarity


    def closest_words(self, word):
        """
        Method to find the closest words for a query. It uses cosine similarity of the
        word vectors and keeps all the words above the cutoff set for the model.
        Args:
            word: query word
        Returns:
            list of words for search filter (query + similar words)
        """
        if word not in self.topic:
            self.topic[word] = set([item[0] for item in self.model.most_similar(word, 
                                    topn=100) if item[1]>self.similarity])
        return [word] + list(self.topic[word])


    def load_data(self, filename):
        """
        Loads the review data from json and outputs a Pandas dataframe and a list of reviews.
        
        reviews: used for building the word counts
        coords: review coordinates used for plotting [date, lati, longi]
        
        Args:
            filename: filepath for the reviews stored in json
        """
        df = pd.read_json(filename)
        self.reviews = df.pop('text').values
        self.coords = df[['date', 'lati', 'longi']]


    def construct_counts(self):
        """
        This method builds an array of word counts from the reviews. 

        counts: word counts matrix from the CountVectorizer model. 
        vocabulary: list of word features from CountVectorizer.
                Limited to words that show up in at least 25 reviews and at most 40 
                percent of the documents.
        """
        print 'constructing counts...'
        start = time.time()
        vect = CountVectorizer(min_df=25, max_df=.4)
        self.counts = vect.fit_transform(self.reviews)
        self.reviews = []
        self.vocabulary = vect.vocabulary_
        print '%s seconds' % (time.time()-start)


    def query(self, term):
        """
        Given a query term, find the closest words and filter the word counts array based on
        these. Return a dataframe of results which will be plotted on the map.
        
        INPUT:
            term: query term
        OUTPUT:
            response: dataframe with [date, lati, longi, flag (0/1), name]
        """
        response = self.coords.copy()
        mask = [self.vocabulary[word] for word in self.closest_words(term) if word in self.vocabulary]
        response['flag'] = (self.counts[:, mask] > 0).astype(int).max(axis=1).toarray()
        response['name'] = term
        return response
 

if __name__ == '__main__':
    rm = ReviewModel(WORD2VEC_MODEL)
    rm.load_data(REVIEWS)
    rm.construct_counts()
    with open('../data/model.pkl', 'w') as f:
        pkl.dump(rm, f)

    print rm.query('bacon')
    