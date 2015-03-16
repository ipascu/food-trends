import pandas as pd
import numpy as np
import cPickle as pkl
from gensim.models import Word2Vec
from sklearn.cluster import AgglomerativeClustering, DBSCAN
from scipy.spatial.distance import pdist, squareform, cosine
import matplotlib.pyplot as plt
import os 
import re
import psycopg2
import time

WORD2VEC_MODEL = '../data/word2vec_model_clean'
CONN = psycopg2.connect(dbname="yelp", user='postgres', host='/tmp', password='postgres')
CURSOR = CONN.cursor()

REGEX = re.compile('[^a-zA-Z-]')

def load_reviews(start_date='2004-10-11', end_date='2015-03-03'):
    '''
    Query SQL with a start and end review date.
    Inputs: start date and end date in the format (yyyy-mm-dd)
    '''     
    query = """ SELECT reviews.yelp_id, reviews.date, reviews.review,
                        restaurants.loc_lat, restaurants.loc_long, restaurants.name
                FROM reviews JOIN restaurants 
                ON reviews.yelp_id = restaurants.yelp_id 
                AND date::DATE > '%s'::DATE 
                AND date::DATE < '%s'::DATE;
            """ % (start_date, end_date)
    print 'Loading reviews...'
    CURSOR.execute(query)
    reviews = pd.DataFrame(CURSOR.fetchall(), 
            columns=['yelp_id', 'date', 'text', 'lat', 'long', 'name'])
    print 'Reviews loaded... %d' % reviews.shape[0]
    return reviews


def word_clusters(query, threshold=.7, topics={}):
    topics[query] = set([term[0] for term in model.most_similar(query, topn=100) if term[1] > threshold])
    

def process_reviews(reviews, topics):
    reviews['tokens'] = reviews['text'].apply(lambda x: set(REGEX.sub(' ', x.lower()).split()))
    for key in topics:
        reviews[key] = reviews['tokens'].apply(lambda x: len(set.intersection(x, topics[key]))>0)
    return reviews[topics.keys() + ['date', 'lat', 'long', 'name']]

def transform_to_timeseries(reviews, topics):
    # round to month
    reviews['date'] = pd.to_datetime(reviews['date']).apply(lambda x: x.replace(day=1))
    categ_share = reviews.groupby('date')[topics.keys()].mean()
    pd.rolling_mean()
    categ_share.plot()
    plt.show()
  

    #return categ_by_day.join(total_by_day, how='inner')

def transform_to_cartodb(data):
    # by month
    data.groupby()
    

if __name__ == '__main__':
    model = Word2Vec.load(WORD2VEC_MODEL)
    
    topics = {}
    queries = ['gmo', 'bacon', 'gluten', 'hipster', 'ramen', 
                'cupcake', 'diarrhea', 'paleo']
    for query in queries:
        word_clusters(query, threshold=.6, topics=topics)

    reviews = load_reviews()
    # take reviews and count if these words are mentioned
    
    clean_reviews = process_reviews(reviews, topics)

    transform_to_timeseries(clean_reviews, topics)
    
    clean_reviews['date'] = pd.to_datetime(clean_reviews['date']).apply(lambda x: x.replace(day=1))
    categ_share = reviews.groupby('date')[topics.keys()].mean()
    categ_share.plot()
    plt.show()
    
