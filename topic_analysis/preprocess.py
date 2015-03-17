import pandas as pd
import psycopg2
import cPickle as pkl
from nltk.corpus import stopwords
import dill
import os 
import time
import re

CONN = psycopg2.connect(dbname="yelp", user='postgres', host='/tmp', password='postgres')
CURSOR = CONN.cursor()
REGEX = re.compile('[^a-zA-Z-]')

STOPWORDS = set(stopwords.words('english') + stopwords.words('spanish') +
                stopwords.words('french') + stopwords.words('italian'))

START_DATE = '2014-12-01'
END_DATE = '2014-12-31'

def clean_doc(doc):
    """
    Pre-process a document before tf-idf. Removes punctuation, stopwords and numbers.
    INPUT: text document.
    """
    doc_clean = REGEX.sub(' ', doc.lower())   
    tokens = doc_clean.split()
    return ' '.join([word for word in tokens if word not in STOPWORDS])


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
    df = df[df['lati'] != 999]	# remove unknown locations
    df['clean_txt'] = df['text'].apply(lambda x: clean_doc(x))
    with open('../data/reviews%s%s.json' % (start_date, end_date), 'w') as f:
        df.to_json(f)


def load_reviews(start_date, end_date):
	''' Load reviews - look for pickled file, if it does not exist, run pickle_reviews '''
	pickle_reviews(start_date, end_date)
	if not os.path.isfile('../data/reviews%s%s.pkl' % (start_date, end_date)):
	    print 'Need to pickle the reviews...'
	    pickle_reviews(start_date, end_date)
	else:
	    print 'Reviews already pickled...'


if __name__ == '__main__':
	load_reviews(start_date=START_DATE, end_date=END_DATE)
