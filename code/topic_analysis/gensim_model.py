import psycopg2
import pandas as pd
import numpy as np
import re
from gensim.models import Word2Vec
from gensim.corpora import Dictionary
import nltk

conn = psycopg2.connect(dbname="yelp", user='postgres', host='/tmp', password='postgres')
c = conn.cursor()

REGEX = re.compile('[^a-zA-Z-]')

TEXTFILE = '../data/reviews.txt'

def load_reviews(filename, start_date='2004-10-11', end_date='2015-03-03'):
        '''
        Query SQL with a start and end review date. Tokenize, remove 
        punctuation and write to filename for input to gensim Word2Vec.
        INPUT: filename, start date and end date in the format (yyyy-mm-dd)
        OUTPUT: None

        '''     
        query = """ SELECT reviews.review FROM reviews
                    WHERE date::DATE > '%s'::DATE 
                    AND date::DATE < '%s'::DATE;
                """ % (start_date, end_date)
        f = open('../data/reviews.txt', 'w')
        c.execute(query)
        counter = 0
        for review in c:
            counter += 1
            if counter % 10000 == 0:
                print '%d reviews so far' % counter
            for sent in nltk.sent_tokenize(review[0]):
                sent_no_punct = REGEX.sub(' ', sent.lower())  
                f.write('%s\n' % sent_no_punct.lower())
        f.close()


def text_stream(filename):
    ''' 
    Function for streaming lines of text from file.
    INPUT: filename - file to be streamed from.
    '''
    with open(filename) as f:
        for line in f:
            yield line.split()


def build_dictionary(filename):
    '''
    Building gensim dictionary from filename.
    INPUT: filename - file with text corpus.
    '''
    print 'building dictionary...'
    txtstream = text_stream(filename)
    dictionary = Dictionary(txtstream)
    dictionary.save('../data/gensim_dictionary')

def build_word2vec(filename):
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
    build_dictionary(TEXTFILE)
