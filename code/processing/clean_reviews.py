from pymongo import MongoClient
from pymongo import errors
from bs4 import BeautifulSoup
import time

client = MongoClient()
db = client.yelp
coll = db.restaurant

def parse_reviews(busi, collection):
    print "parsing reviews for " + busi['name']

    business = collection.find_one({"id" : busi['id'] })
    for review in business['reviews']:
        soup = BeautifulSoup(review['html'], "html.parser")
 
        if soup.find(itemprop = "reviewRating"):
            review['rating'] = soup.find(itemprop = "ratingValue")['content']
            review['date'] = soup.find(itemprop = "datePublished")['content']
            review['text'] = soup.find(itemprop = "description").text    
        collection.save(business)

if __name__ == '__main__':
    for busi in coll.find({},{name:1, id:1}):
        start = time.time()
        parse_reviews(busi, coll)
        print '%d seconds' % (time.time() - start)
        #five_stars = filter(lambda x: x['rating'] == '5.0', coll.find_one({"id" : busi['id']})['reviews'])

