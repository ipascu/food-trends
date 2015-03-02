import search as yelp
from pymongo import MongoClient
from pymongo import errors
import time


class GetMeta(object):

    def __init__(self, database, table_name,
                 key, secret_key, token, secret_token, params):
        client = MongoClient()
        self.database = client[database]
        self.table = self.database[table_name]
        self.key = key
        self.secret_key = secret_key
        self.token = token
        self.secret_token = secret_token
        self.params = params

    def make_request(self):
        """Using the search terms and API keys, connect and get from Yelp API"""
        return yelp.request(self.params, self.key, self.secret_key,
                            self.token, self.secret_token)

    def insert_business(self, rest):
        """
        :param rest: Dictionary object containing meta-data to be inserted in Mongo
        :return: None

        Inserts dictionary into MongoDB
        """
        if not self.table.find_one({"id": rest['id']}):
            # Make sure all the values are properly encoded
            for field, val in rest.iteritems():
                if type(val) == str:
                    rest[field] = val.encode('utf-8')

            try:
                print "Inserting restaurant " + rest['name']
                self.table.insert(rest)
            except errors.DuplicateKeyError:
                print "Duplicates"
        else:
            print "In collection already"

    def run(self):
        try:
            response = self.make_request()
            # The number of total results returned
            total_num = response['total']
            print 'Total number of entries for the query', total_num
            # can only increase offset to 1000        
            while self.params['offset'] < total_num:
                response = self.make_request()
                try:
                    for business in response['businesses']:
                        self.insert_business(business)
                except:
                    print 'TOO MANY RESTAURANTS IN CATEGORY:'
                    print self.params['category_filter']
                    print response
                self.params['offset'] += 20
                time.sleep(0.5)
        except:
            print response, self.params['category_filter']
        # The existing number of results
        #total_results = self.table.find().count()


def main():
    DB_NAME = 'yelp'
    TABLE_NAME = 'restaurant'

    # KEY = ""
    # SECRET_KEY = ""
    # TOKEN = ""
    # SECRET_TOKEN = ""

    categories = []
    with open('restaurants.txt') as f:
        for line in f:
            temp = line.split(",")
            temp = temp[0].split("(")
            categories.append(temp[-1])

    # searching by category to get fewer than 1000 results
    for category in categories:
        PARAMS = {'location': 'San+Francisco',
                  'term': 'restaurants',
                  'category_filter': category,
                  'limit': 20,
                  'offset': 0}

        yelp_meta = GetMeta(DB_NAME, TABLE_NAME,
                            KEY, SECRET_KEY, TOKEN,
                            SECRET_TOKEN, PARAMS)
        yelp_meta.run()
                        

if __name__ == '__main__':
    main()
