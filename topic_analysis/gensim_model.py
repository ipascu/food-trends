"""
This module trains the Word2Vec model on restaurant reviews. 
"""

import psycopg2
import re
from gensim.models import Word2Vec
import nltk

CONN = psycopg2.connect(dbname="yelp", user='postgres', host='/tmp', password='postgres')
CURSOR = CONN.cursor()

REGEX = re.compile('[^a-zA-Z-]')

TEXTFILE = '../data/reviews.txt'

def load_reviews(filename, start_date='2004-10-11', end_date='2015-03-03'):
    '''
    Function for loading reviews from the Yelp SQL database for a range of dates.
    Reviews are parsed, split into sentences and stripped of punctuation. The final
    output is written to a text file given by filename with one sentence per line.
    
    INPUT: 
        filename - 
        start date - 
        end date - in the format (yyyy-mm-dd)
    OUTPUT: None
    '''     
    query = """ SELECT reviews.review FROM reviews
                WHERE date::DATE > '%s'::DATE 
                AND date::DATE < '%s'::DATE;
            """ % (start_date, end_date)
    f = open('../data/reviews.txt', 'w')
    CURSOR.execute(query)
    counter = 0
    for review in CURSOR:
        counter += 1
        if counter % 10000 == 0:
            print '%d reviews so far' % counter
        for sent in nltk.sent_tokenize(review[0]):
            sent_no_punct = REGEX.sub(' ', sent.lower())  
            f.write('%s\n' % sent_no_punct.lower())
    f.close()


def text_stream(filename):
    ''' 
    Function for streaming lines of text from a text file which has one sentence per line.
    INPUT: filename - name of text file with the training text for the model.
    '''
    with open(filename) as f:
        for line in f:
            yield line.split()


def build_word2vec(filename):
    '''
    Function that builds the word2vec vocabulary and model using gensim.
    INPUT: filename - text file that contains the training text.
    '''
    print 'building vocabulary...'
    model = Word2Vec(min_count=10)
    txtstream = text_stream(filename)
    model.build_vocab(txtstream)

    print 'training word2vec...'
    txtstream = text_stream(filename)
    model.train(txtstream)
    model.save('../data/word2vec_modelf')


if __name__ == '__main__':
    load_reviews(TEXTFILE)
    build_word2vec(TEXTFILE)
    
