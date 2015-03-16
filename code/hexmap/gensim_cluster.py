import pandas as pd
import numpy as np
import psycopg2
import cPickle as pkl
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from nltk.corpus import stopwords
from gensim.models import Word2Vec
from sklearn.cluster import AgglomerativeClustering, DBSCAN
from sklearn.neighbors import NearestNeighbors
from scipy.spatial.distance import pdist, squareform, cosine
import os 
import time
import re

CLUSTERS_FILE = '../pickles/clusters.pkl'
MENUS_FILE = '../pickles/menu_corpus.pkl'
WORD2VEC_MODEL = '../data/word2vec_modelf'
DICT_FILE = '../data/gensim_dictionary'
REVIEWS_PKL = '../data/reviews.pkl'
THEMES = ['gmo', 'hipster', 'bacon', 'cronut', 'ipa', 'diarrhea', 
          'toast', 'ramen', 'bitters', 'paleo', 'gluten', 'cupcake',
          'dirty', 'vacation', 'heartburn', 'tikka', 'kimchi']

CONN = psycopg2.connect(dbname="yelp", user='postgres', host='/tmp', password='postgres')
CURSOR = CONN.cursor()
REGEX = re.compile('[^a-zA-Z-]')

STOPWORDS = set(stopwords.words('english') + stopwords.words('spanish') +
                stopwords.words('french') + stopwords.words('italian'))

def cosine_distance(x, y):
    '''
    cosine distance for clustering
    INPUT: two vectors
    OUPUT: cosine distance
    '''
    return cosine(x, y)

class ReviewModel(object):
    """docstring for ReviewModel"""
    def __init__(self, model_file=WORD2VEC_MODEL, similarity=.65):
        self.model = Word2Vec.load(model_file)
        self.topic = {}
        self.similarity = similarity
        self.themes = THEMES

    def closest_words(self, word):
        if word not in self.topic:
            self.topic[word] = set([item[0] for item in self.model.most_similar(word, 
                                    topn=100) if item[1]>self.similarity])
        return [word] + list(self.topic[word])

    def define_queries(self):
        ''' 
        define the set of queries to allow for the model.
        constructed from words in the menus plus additional terms of interest
        '''
        foods = get_food_vocabulary(MENUS_FILE, max_features=100)                   # get top food words from menus
        self.queries = set.intersection(set(foods), set(self.model.index2word))     # restrict to words in the word2vec model
        self.queries = set.union(self.queries, set(self.themes))


    def _load_reviews(self, start_date, end_date):
        ''' Load reviews - look for pickle file, if it does not exist, run pickle_reviews '''
        if not os.path.isfile('../data/reviews%s%s.pkl' % (start_date, end_date)):
            print 'Need to pickle the reviews...'
            return pickle_reviews(start_date, end_date)
        else:
            print 'Reviews already pickled...'
            return pkl.load(open('../data/reviews%s%s.pkl' % (start_date, end_date)))

    def load_data(self, start_date, end_date):
        df = self._load_reviews(start_date, end_date)
        self.reviews = df.pop('text').values
        self.coords = df[['date', 'lati', 'longi']]

    def construct_counts(self):
        print 'constructing counts...'
        start = time.time()
        vect = CountVectorizer(min_df=50, max_df=.4)
        self.counts = vect.fit_transform(self.reviews)
        self.reviews = []
        self.vocabulary = vect.vocabulary_
        print '%s seconds' % (time.time()-start)

    def query(self, term):
        response = self.coords.copy()
        mask = [self.vocabulary[word] for word in self.closest_words(term) if word in self.vocabulary]
        response['flag'] = (self.counts[:, mask] > 0).max(axis=1).toarray().astype(int)
        response['name'] = term
        # data to export
        return response

def clean_doc(doc):
    """
    Pre-process a document before tf-idf. Removes punctuation, stopwords and numbers.
    INPUT: text document.
    """
    doc_clean = REGEX.sub(' ', doc.lower())   
    tokens = doc_clean.split()
    return ' '.join([word for word in tokens if word not in STOPWORDS])


def get_food_vocabulary(filename, max_features=100, max_df=.3):
    with open(filename) as f:
        corpus = pkl.load(f)
    clean_docs = [clean_doc(doc) for doc in corpus]
    vect = TfidfVectorizer(max_features=max_features, max_df=max_df)
    tfidf = vect.fit(clean_docs)
    return tfidf.get_feature_names()


def pickle_reviews(start_date, end_date):
        '''
        Query SQL with a start and end review date. Tokenize, remove 
        punctuation and pickle the dataframe.
        INPUT: filename, start date and end date in the format (yyyy-mm-dd)
        OUTPUT: None

        '''     
        query = """ SELECT reviews.yelp_id, reviews.date, reviews.review,
                        restaurants.loc_lat, restaurants.loc_long, restaurants.name
                    FROM reviews JOIN restaurants 
                    ON reviews.yelp_id = restaurants.yelp_id 
                    AND date::DATE >= '%s'::DATE 
                    AND date::DATE <= '%s'::DATE;
                """ % (start_date, end_date)
        CURSOR.execute(query)
        df = pd.DataFrame(CURSOR.fetchall(), columns=['yelp_id', 
                                'date', 'text', 'lati', 'longi', 'name'])
        print 'Reviews loaded... %d' % df.shape[0]
        df['clean_txt'] = df['text'].apply(lambda x: clean_doc(x))
        with open('../data/reviews%s%s.pkl' % (start_date, end_date), 'w') as f:
            pkl.dump(df, f)
        return df
        


if __name__ == '__main__':
    rm = ReviewModel()
    rm.load_data(start_date='2014-12-01', end_date='2014-12-31')
    rm.construct_counts()
    with open('../data/model_small.pkl', 'w') as f:
        pkl.dump(rm, f)
    # construct a set of word groups of interest    
    #print 'Constructing query vocabulary...'
    #rm.define_queries()
    print 'query response...'
    start = time.time()
    r = rm.query('coffee')
    print '%d seconds' % (time.time()-start)
    print STOPHERE


    

    # for term in themes:
    #     counts = CountVectorizer(vocabulary=rm.closest_words(term)).fit_transform(reviews)
    #     df[term] = np.any(counts.toarray()>0, axis=1)

    # #df['date_month'] = pd.to_datetime(df['date']).apply(lambda x: x.replace(day=1))
    # df.to_csv('../data/final_all_trends_subset.csv', 
    #     columns=themes + ['yelp_id', 'date', 'lat', 'long', 'name'])
    

    # df = pd.read_csv('../data/final_all_trends_subset.csv')
    # for flag in ['bacon']:
    #     data = df[['date', 'lat', 'long', flag]].rename(columns={'lat': 'lati', 'long': 'longi'})
    #     data['flag'] = data[flag].astype(int)
    #     data['name'] = flag
    #     data[:4000].to_csv('../data/small.csv', columns=['lati', 'longi', 'date', 'flag', 'name'], index=False)


    # df['date'] = pd.to_datetime(df['date']).apply(lambda x: x.replace(day=1))
    # # fix computations for normalizations
    # # aggregate by date
    # df = df[df['lat']!=999]     # filter out invalid locations, very few
    # group_date = df.groupby('date')

    # df_date = group_date[themes].sum()
    # df_date['total'] = group_date['gmo'].count()
    # #df_date.set_index('date', inplace=True)
    # df_month = df_date.resample(rule='M', how=sum)
    # #df_month.to_csv('../data/time_trends.csv')

    # pd.rolling_mean((df_month[themes] / df_month['total']), window=3, center=True).plot()

    # pd.rolling_mean((df_month[['gmo']] / df_month['total']), window=3, center=True).plot()
    # plt.show()

    # # group_coords = df.groupby(['date_month', 'lat', 'long'])
    # # df_coords = group_coords[themes].sum()
    # # df_coords['total'] = group_coords['text'].count()
    # # df_coords.to_csv('../data/map_trends.csv')   