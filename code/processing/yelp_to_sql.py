'''
this code will process the mongo -> postgres yelp data
creating one table with restaurant meta data
creating one long table with restaurant id, date, rating, review text
'''
from pymongo import MongoClient
from pymongo import errors
import psycopg2

mongoclient = MongoClient()
DB_NAME = 'yelp'
TABLE_NAME = 'restaurant'

def make_restaurant_table():
	c.execute('DROP TABLE IF EXISTS restaurants;')
	c.execute('''CREATE TABLE restaurants
		(mongoid TEXT PRIMARY KEY,
		yelp_id TEXT,
		rating REAL,
		review_count INT,
		name 	TEXT,
		url 	TEXT,
		contact_phone TEXT,
		categories TEXT,
		is_closed BOOLEAN,
		loc_city TEXT,
		loc_postalcode TEXT,
		loc_state char(2),
		loc_address TEXT,
		loc_lat REAL,
		loc_long REAL);''')

def make_reviews_table():
	c.execute('DROP TABLE IF EXISTS reviews;')
	c.execute(''' CREATE TABLE reviews
		(mongoid TEXT,
		yelp_id TEXT,
		rating INT,
		date TEXT,
		review TEXT);''')

def insert_restaurant(r):
	categories = ';'.join([cat[0] for cat in r['categories']])
	location = r['location']
	phone = r.get('phone', '')
	postal_code = location.get('postal_code', '')
	coordinate = location.get('coordinate', {})
	# need to filter these later
	latitude = coordinate.get('latitude', '999')
	longitude = coordinate.get('longitude', '999')
	name = r['name'].encode('ascii', 'ignore')
	address = ';'.join(location.get('address', ''))
	c.execute(
			""" INSERT INTO restaurants (mongoid, yelp_id, rating, review_count, \
			name, url, contact_phone, categories, \
			is_closed, loc_city, loc_postalcode, \
			loc_state, loc_address, loc_lat, loc_long) VALUES (%s, %s, %s, %s, %s, 
			%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""" ,
				( str(r['_id']), r['id'], r['rating'], r['review_count'], name,
				r['url'], phone, categories, r['is_closed'], location['city'],
				postal_code, location['state_code'], address,
				float(latitude), 
				float(longitude)))

def insert_reviews(r):
	for review in r['reviews']:
		c.execute(
			""" INSERT INTO reviews (mongoid, yelp_id, rating, 
				date, review) VALUES (%s, %s, %s, %s, %s);""",
			( str(r['_id']), r['id'], int(float(review['rating'])), review['date'], 
				review['text'].encode('ascii', 'ignore') ) )
			

if __name__ == '__main__':
	coll = mongoclient.yelp.restaurant

	conn = psycopg2.connect(dbname="yelp", user='postgres', host='/tmp', password='postgres')
	c = conn.cursor()
	make_restaurant_table()
	make_reviews_table()

	# query mongo and insert restaurants into postgres
	restaurants = coll.find()
	for r in restaurants:
		print "inserting: ", r['name'].encode('ascii', 'ignore')
		insert_restaurant(r)
		insert_reviews(r)
		# make changes to the database persistent
		conn.commit()

	# close communications with the database
	c.close()
	conn.close()