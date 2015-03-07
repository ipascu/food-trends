import cPickle as pkl
import psycopg2

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
		self.H = pkl.load(open(H_pkl))
		self.num_topics = self.H.shape[0]
		self.reviews = None		# this will be a pandas DataFrame of the reviews pulled
		self.tfidf = None
		self.similarity = None

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
		self.similarity = np.dot(self.tfidf, self.H.T)

	def review_transform(self):
		''' Get tfidf matrix for the reviews using the pickled vectorizer
		Find topic similarity.
		'''
		self.tfidf = self.vectorizer.transform(self.reviews['text'].values)


if __name__ == '__main__':
	vect_pkl = '../pickles/vect.pkl'
	H_pkl = '../pickles/H.pkl'
	trend = TrendAnalyzer(vect_pkl, H_pkl)
	trend.get_reviews(start_date='2014-02-01', end_date='2014-02-10')
	trend.review_transform()
	trend.get_reviews_similarity()



