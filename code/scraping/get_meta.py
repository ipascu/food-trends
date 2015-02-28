import yelp.search as yelp
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

        # The number of total results returned
        total_num = self.make_request()['total']
        print 'Total number of entries for the query', total_num

        # The existing number of results
        total_results = self.table.find().count()

        while total_results < total_num and self.params['offset'] < total_num:
            response = self.make_request()

            for business in response['businesses']:
                self.insert_business(business)

            self.params['offset'] += 20
            time.sleep(1)

def main():
    DB_NAME = 'yelp'
    TABLE_NAME = 'restaurant'

    KEY = "FnyzM_idXpBcHLaEwQArgA"
    SECRET_KEY = "u57LDQDWYjf6rEfrWnQZ1T5wc0Q"
    TOKEN = "I9ZtcBw249hiqSSNqzFjK5iQcES4YlN_"
    SECRET_TOKEN = "tCFZujoNsvfK44O4XIFefXFVRsU"

    PARAMS = {'location': 'San Francisco',
              'term': 'restaurants',
              'limit': 20,
              'offset': 0}

    yelp_meta = GetMeta(DB_NAME, TABLE_NAME,
                        KEY, SECRET_KEY, TOKEN,
                        SECRET_TOKEN, PARAMS)
    yelp_meta.run()

if __name__ == '__main__':
    main()
