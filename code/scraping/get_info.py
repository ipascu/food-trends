from pymongo import MongoClient
from pymongo import errors
from bs4 import BeautifulSoup
import requests

import time
import pdb


client = MongoClient()
db = client.yelp2
coll = db.restaurant

# key = "xxxx"
# c_secret = "xxxx"
# token = "xxxx"
# t_secret = "xxxx"

def get_npages(url):
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    pages = soup.find('div', class_="page-of-pages").text.split()[-1]
    return int(pages)

def get_curr_rev_cnt(busi):
    return len(busi.get('reviews',[]))

def try_requests(url):
    counter = 0
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.text
        else:
            while counter < 3 or r.status_code != 200:
                time.sleep(5)
                r = requests.get(url)
                counter += 1
    except:
        print 'Could not access link %s' % url
        print r.status_code
        return ""


def get_reviews(busi, collection):
    print "getting reviews for " + busi['name']

    if get_curr_rev_cnt(busi) < busi.get('review_count', 0):
        collection.update({"id" : busi['id']}, { '$set' : { 'reviews': [] } })

        npages = get_npages(busi['url'])
        for page in xrange(npages):
            index = page * 40
            url = '%s?start=%d' % (busi['url'], index)
            soup = BeautifulSoup(requests.get(url).text, "html.parser")
            rev = soup.find_all('div', class_ = 'review')
        
            #collection.update({"id" : busi['id']}, { '$set' : { 'reviews': [ { 'html' : str(item) } for item in rev ]} })
            collection.update({"id" : busi['id']}, { '$push' : { 'reviews': { '$each': [ { 'html' : str(item) } for item in rev ]}}})
            time.sleep(1)

def parse_reviews(busi, collection):
    print "getting stars for " + busi['name']

    business = collection.find_one({"id" : busi['id'] })
    for review in business['reviews']:
        soup = BeautifulSoup(review['html'], "html.parser")
 
        if soup.find(itemprop = "reviewRating"):
            review['rating'] = soup.find(itemprop = "ratingValue")['content']
            #collection.save(business)
            
if __name__ == '__main__':
    for busi in coll.find({'name': 'De Afghanan Kabob House'}):
        get_reviews(busi, coll)
    #r2 = parse_reviews(busi, coll)
    #for busi in coll.find():
    #     get_reviews(busi, coll)
    #     parse_reviews(busi, coll)
    #     # five_stars = filter(lambda x: x['rating'] == '5.0', coll.find_one({"id" : busi['id']})['reviews'])