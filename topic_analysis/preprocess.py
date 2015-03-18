import pandas as pd
import psycopg2
from nltk.corpus import stopwords
import os
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
    Pre-process a document before word counts. Removes punctuation,
    stopwords and numbers.
    INPUT: string to process. Returns the cleaned text.
    """
    doc_clean = REGEX.sub(' ', doc.lower())
    tokens = doc_clean.split()
    return ' '.join([word for word in tokens if word not in STOPWORDS])


def clean_df(df):
    """
    This function takes in a dataframe of reviews created from SQL query
    for cleaning:
        - filters the unknown locations
        - calls clean_doc to parse the text
    INPUT: dataframe to clean
    OUTPUT: cleaned dataframe
    """
    df = df[df['lati'] != 999]  # remove unknown locations
    df['clean_txt'] = df['text'].apply(lambda x: clean_doc(x))
    return df


def reviews_to_json(start_date, end_date, update=False):
    """
    Query SQL with a start and end review date for the map plots.
    Tokenize, remove punctuation and export the cleaned text to a json.
    INPUT: start_date: Query start date in 'yyyy-mm-dd' format
           end_date: Query end date in 'yyyy-mm-dd' format
           update: Flag to overwrite the current extract if it already exists.
    OUTPUT: None
    """
    filename = '../data/reviews%s%s.json' % (start_date, end_date)

    if update or not os.path.isfile(filename):
        query = """ SELECT reviews.date, reviews.review, restaurants.loc_lat,
                            restaurants.loc_long, restaurants.name
                    FROM reviews JOIN restaurants
                    ON reviews.yelp_id = restaurants.yelp_id
                    AND date::DATE >= '%s'::DATE
                    AND date::DATE <= '%s'::DATE;
                """ % (start_date, end_date)

        CURSOR.execute(query)

        df = clean_df(pd.DataFrame(CURSOR.fetchall(), columns=['date',
                                    'text', 'lati', 'longi', 'name']))

        print 'Reviews loaded... %d' % df.shape[0]
        with open('../data/reviews%s%s.json' % (start_date, end_date), 'w') as f:
            df.to_json(f)

    else:
        print 'Reviews already exported...'


if __name__ == '__main__':
    reviews_to_json(start_date=START_DATE, end_date=END_DATE, update=True)
