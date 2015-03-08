import psycopg2
import pandas as pd
import csv

if __name__ == '__main__':
	''' testing SQL aggregations by restaurant / month. 
	This code just pulls the total number of reviews by restaurant / month.
	'''
	conn = psycopg2.connect(dbname="yelp", user='postgres', host='/tmp', password='postgres')
	c = conn.cursor()

	# query with aggregation by month
	# query = """ SELECT t.yelp_id, t.nreviews, t.date_month, loc_lat, loc_long
	# 			FROM restaurants
	# 			JOIN (SELECT yelp_id, COUNT(*) AS nreviews,
	# 				DATE_TRUNC('month', date::DATE) AS date_month
	# 				FROM reviews 
	# 				GROUP BY date_month, yelp_id) t
	# 			ON restaurants.yelp_id = t.yelp_id;
	# 		"""

	query = """SELECT reviews.yelp_id, reviews.rating, reviews.date, reviews.review,
					restaurants.loc_lat, restaurants.loc_long, restaurants.name
				FROM reviews JOIN restaurants
				ON review LIKE '%gluten%' AND reviews.yelp_id = restaurants.yelp_id
			"""
	
	c.execute(query)

	r = c.fetchall()
	df = pd.DataFrame(r, columns = ['yelp_id', 'rating', 'date', 'review', 'latitude', 'longitude'])
	df = df[(df['latitude'] != 999) & (df['longitude']!=999)]

	df.to_csv('../../maps/gluten.csv', columns=['latitude', 'longitude', 'date', 'name'], index=False)
	
	# Output for CartoDB
	# with open('review_intensity.csv', 'wb') as outfile:
	# 	writer = csv.writer(outfile, delimiter=',')
	# 	for record in c:
	# 		writer.writerow(record)
	# 