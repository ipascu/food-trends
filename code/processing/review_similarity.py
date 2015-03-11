from menu_nlp import ExtractFoodTopics, clean_doc
import cPickle as pkl
import psycopg2
import pandas as pd
import numpy as np
import re

'''
Plan:
NMF on menus - get topics (DONE)
    - visualize     (word clouds)
Get sample of reviews. (DONE)
Compute similarity to menu topics. (almost)
Figure out how to aggregate over time.
Figure out how to aggregate for plotting.
'''

'''
    Use the food topics based on menus to analyze review trends.
'''

conn = psycopg2.connect(dbname="yelp", user='postgres', host='/tmp', password='postgres')
c = conn.cursor()

class TrendAnalyzer(object):
    def __init__(self, topics_model):
        self.model = topics_model
        self.reviews = None     # this will be a pandas DataFrame of the reviews pulled

    def load_reviews(self, start_date='2004-10-11', end_date='2015-03-03'):
        '''
        Query SQL with a start and end review date.
        Inputs: start date and end date in the format (yyyy-mm-dd)
        '''     
        query = """ SELECT * FROM reviews
                    WHERE date::DATE > '%s'::DATE 
                    AND date::DATE < '%s'::DATE;
                """ % (start_date, end_date)
        c.execute(query)
        self.reviews = pd.DataFrame(c.fetchall(), columns=['mongoid', 
                        'yelp_id', 'rating', 'date', 'text'])
        print 'Reviews loaded... %d' % self.reviews.shape[0]

    def reviews_latent_topics(self):
        docs = self.reviews['text'].values
        clean_docs = [clean_doc(doc) for doc in docs]
        tfidf = self.model.vect.transform(clean_docs)
        self.latent_weights = self.model.nmf.transform(tfidf)
    
    def display_review_topic(self, n=10, n_top_words=10):
        temp = self.tfidf[:n, :].toarray()
        top_n_index = np.argsort(temp, axis=1)[:,-n_top_words:]
        top_words = [[self.words[i] for i in row] for row in top_n_index]
        for i in xrange(temp.shape[0]):
            print '\n'
            print self.reviews['text'][i]
            print top_words[i]
        
if __name__ == '__main__':
    food_topics_file = '../pickles/food_topics.pkl'
    review_topics_file = '../pickles/review_topics.pkl'
    with open(food_topics_file) as f:
        topics_model = pkl.load(f)

    trend = TrendAnalyzer(topics_model)
    trend.load_reviews()
    trend.reviews_latent_topics()

    with open(review_topics_file, 'w') as f:
        pkl.dump(trend, f)

    #trend.reviews['topic_weight'] = np.max(topics, axis=1)
    #trend.reviews['topic'] = np.argmax(topics, axis=1)

