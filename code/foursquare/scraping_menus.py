import foursquare
from pymongo import MongoClient
from pymongo import errors
import time

mongoclient = MongoClient()

DB_NAME = 'foursquare'
TABLE_NAME = 'venues'

client_id='XXXX'
client_secret='XXXX' 

class GetFoursquare(object):
    def __init__(self, database, table_name):
        self.fsqclient = foursquare.Foursquare(client_id=client_id, client_secret=client_secret)
        self.database = mongoclient[database]
        self.table = self.database[table_name]
        self.params = {}

    def make_params(self, ll='', near='', query='', limit=50, intent='browse', 
        categoryId='4d4b7105d754a06374d81259', radius=250):
        # categoryId https://developer.foursquare.com/categorytree
        # food - 4d4b7105d754a06374d81259
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
        """Using the search terms and API keys, connect and get from FourSquare API"""
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
                if type(val) == str:
                    venue[field] = val.encode('utf-8', 'ignore')
            try:
                print "Inserting restaurant " + venue["name"]
                self.table.insert(venue)
            except errors.DuplicateKeyError:
                print "Duplicates"
            except:
                print "Other error"
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

    def populate_venues(self, location_list):
        ''' use a location list to query foursquare and populate a MongoDB database '''
        for loc in location_list[11::15]:
            self.make_params(ll=loc, radius=400, intent='browse', query='restaurant')
            self.run_search()

    def city_start(self, city='San Francisco', radius=500):
        '''
        Explore an entire city. Useful for getting an initial
        set of locations in a new city.
        '''
        self.make_params(intent='explore', query='restaurant', near=city, radius=radius)
        self.run_search()

def get_locations(city='San Francisco'):
    coll = mongoclient.foursquare.venues
    r = coll.find({'location.city':city}, {'_id':0, 'location.lat':1, 'location.lng':1})
    return [(rest['location']['lat'], rest['location']['lng']) for rest in r]

if __name__ == '__main__':
    # ['Chicago', 'San Francisco', 'Austin', 'New York', 'Los Angeles']
    cities = ['Philadelphia', 'Chicago', 'San Francisco']
    fsq = GetFoursquare(DB_NAME, TABLE_NAME)
    for city in cities:
        fsq.city_start(city, radius=5000)
        fsq.populate_venues(get_locations(city))
    fsq.get_menu_info()
