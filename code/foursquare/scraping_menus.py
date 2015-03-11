import foursquare
from pymongo import MongoClient, errors
import time

mongoclient = MongoClient()

DB_NAME = 'foursquare'
TABLE_NAME = 'venues'

with open('../keys/foursquare.txt') as f:
    CLIENT_ID, CLIENT_SECRET = f.read().split(',')

class GetFoursquare(object):
    def __init__(self, database, table_name):
        self.fsqclient = foursquare.Foursquare(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        self.database = mongoclient[database]
        self.table = self.database[table_name]
        self.params = {}

    def make_params(self, ll='', near='', query='', limit=50, intent='browse', 
        categoryId='4d4b7105d754a06374d81259', radius=250): 
        """ 
        INPUT: search parameters for the foursquare API
               Source for categoryId: https://developer.foursquare.com/categorytree
        OUTPUT: dictionary of parameters.
        """
        self.params={}
        self.params={'query': query,
                    'limit': limit, 
                    'intent': intent, 
                    'categoryId': categoryId,
                    'radius': radius}
        if ll != '':
            self.params['ll'] = '%.5f, %.5f' % ll
        if near != '':
            self.params['near'] = near 

    def run_search(self):
        """
        Using the search terms and API keys, connect and get list of venues from FourSquare API
        """
        response = self.fsqclient.venues.search(params=self.params)
        print 'Total number of venues ', len(response['venues'])
        for venue in response['venues']:
            self.insert_venue(venue)

    def insert_venue(self, venue):
        """
        Inserts dictionary into MongoDB. Checks that the restaurant does not already exist.
        """
        if not self.table.find_one({"id": venue["id"]}):
            for field, val in venue.iteritems():
                if isinstance(val, basestring):
                    venue[field] = val.encode('ascii', 'ignore')
            try:
                print "Inserting restaurant id: %s, name: %s" % (venue["id"], venue["name"])
                self.table.insert(venue)
            except errors.DuplicateKeyError:
                print "Duplicates"
        else:
            print "In collection already"

    def get_menu_info(self):
        """
        Find the restaurants in the foursquare database for which hasMenu is true, but 
        they do not yet have menu data stored from the API. Call the venues.menu API with 
        these restaurant ids.
        """
        to_process = self.table.find({'$and': [{'hasMenu':True}, {'menus.count':{'$exists':0}}]})
        counter = 0
        for venue in to_process:
            counter += 1
            print venue['name']
            request = self.fsqclient.venues.menu(venue['id'])
            venue['menus'] = request['menu']['menus']
            self.table.save(venue)
            if counter % 2500 == 0:
                print counter
                time.sleep(1500)

    def populate_venues(self, location_list, radius=250, intent='search', query=''):
        """ 
        Use a location list (lat,long) to query foursquare and populate a MongoDB database 
        """
        for loc in location_list[::250]:
            self.make_params(ll=loc, radius=radius, intent=intent, query=query)
            self.run_search()

    def city_start(self, city='San Francisco', radius=500):
        """
        Explore an entire city. Useful for getting an initial
        set of locations in a new city.
        """
        self.make_params(intent='explore', query='restaurant', near=city, radius=radius)
        self.run_search()

    def get_locations(self, city='San Francisco'):
        """
        Get list of locations to query for more venues from the locations in the database.
        Can also use an external source or a grid of lat, long for each city.
        """
        r = self.table.find({'location.city':city}, {'_id':0, 'location.lat':1, 'location.lng':1})
        return [(rest['location']['lat'], rest['location']['lng']) for rest in r]

if __name__ == '__main__':
    cities = ['Portland', 'Seattle', 'Los Angeles', 'Madison', 'Denver', 'Miami', 
        'Phoenix', 'Houston', 'San Diego', 'Atlanta', 'Austin', 'Philadelphia',
        'Chicago', 'San Francisco', 'Cambridge', 'Boston']
    fsq = GetFoursquare(DB_NAME, TABLE_NAME)
    
    for city in cities:
        fsq.city_start(city, radius=7500)
        fsq.populate_venues(fsq.get_locations(city))
    fsq.get_menu_info()
