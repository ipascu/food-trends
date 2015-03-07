import cPickle as pkl
import psycopg2
import pandas as pd
import numpy as np

'''
Plan:

NMF on menus - get topics
	- visualize 
Get sample of reviews.
Compute similarity to menu topics.
Figure out how to aggregate over time.
Figure out how to aggregate for plotting.
'''

conn = psycopg2.connect(dbname="yelp", user='postgres', host='/tmp', password='postgres')
c = conn.cursor()

class TrendAnalyzer(object):
	'''
	Loads the vectorizer and H matrix necessary for food trend analysis.
	'''
	def __init__(self, vect_pkl, H_pkl):
		self.vectorizer = pkl.load(open(vect_pkl))
		self.words = self.vectorizer.get_feature_names()
		self.H = pkl.load(open(H_pkl))
		self.num_topics = self.H.shape[0]
		self.reviews = None		# this will be a pandas DataFrame of the reviews pulled
		self.tfidf = None

	def get_reviews(self, start_date='2012-01-01', end_date='2012-02-01'):
		'''
		Query SQL with a start and end review date.
		Inputs: start date and end date in the format (yyyy-mm-dd)
		'''		
		query = """ SELECT * FROM reviews
				WHERE date::DATE > '%s'::DATE AND date::DATE < '%s'::DATE;
				""" % (start_date, end_date)

		c.execute(query)
		self.reviews = pd.DataFrame(c.fetchall(), columns=['mongoid', 'yelp_id', 'rating', 
			'date', 'text'])

	def get_reviews_similarity(self):
		self.similarity = np.dot(self.tfidf.toarray(), self.H.T)

	def review_transform(self):
		''' Get tfidf matrix for the reviews using the pickled vectorizer
		Find topic similarity.
		'''
		self.tfidf = self.vectorizer.transform(self.reviews['text'].values)

	def display_review_topic(self, n=10, n_top_words=10):
		temp = self.tfidf[:n, :].toarray()
		top_n_index = np.argsort(temp, axis=1)[:,-n_top_words:]
		top_words = [[self.words[i] for i in row] for row in top_n_index]
		for i in xrange(temp.shape[0]):
			print '\n'
			print self.reviews['text'][i]
			print top_words[i]
		# self.words(np.argsort(temp, axis=1))[::-1][:n_top_words]
		# topics_dicts = []
	 	#    n_topics = H.shape[0]
	 	#    for i in xrange(n_topics):
	 	#        k, v = zip(*sorted(zip(words, H[i]),
		#                           key=lambda x: x[1])[:-n_top_words:-1])
	 	#        val_arr = np.array(v)
	 	#        norms = val_arr / np.sum(val_arr)
	 	#        topics_dicts.append(dict(zip(k, norms * 100)))
	 	#    return topics_dicts
	    



if __name__ == '__main__':
	vect_pkl = '../pickles/vect.pkl'
	H_pkl = '../pickles/H.pkl'
	trend = TrendAnalyzer(vect_pkl, H_pkl)
	trend.get_reviews(start_date='2014-02-01', end_date='2014-02-10')
	trend.review_transform()
	trend.get_reviews_similarity()



