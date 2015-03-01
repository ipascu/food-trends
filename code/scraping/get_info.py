from pymongo import MongoClient
from pymongo import errors
from bs4 import BeautifulSoup
import requests

import time
import pdb


client = MongoClient()
db = client.yelp
coll = db.restaurant

auth = requests.auth.HTTPProxyAuth('krdooley', 'qwerty00')
proxies = {'http': 'http://us-il.proxymesh.com:31280'}


def get_npages(url):
    text = try_requests(url)
    if len(text) > 0:
        soup = BeautifulSoup(text, "html.parser")
        pages = soup.find('div', class_="page-of-pages").text.split()[-1]
        return int(pages)
    return 0

def get_curr_rev_cnt(busi):
    return len(busi.get('reviews',[]))

def try_requests(url):
    counter = 0
    try:
        r = requests.get(url, proxies=proxies, auth=auth)
        if r.status_code == 200:
            return r.text
        else:
            while counter < 3:
                counter += 1
                time.sleep(5)
                r = requests.get(url, proxies=proxies, auth=auth)
                if r.status_code == 200:
                    return r.text
            print 'Could not access link %s' % url
            print r.status_code
            return ""
    except:
        print 'Could not access link %s' % url
        return ""


def get_reviews(busi, collection):
    print "getting reviews for " + busi['name']
    
    rev = []    
    if get_curr_rev_cnt(busi) < busi.get('review_count', 0):
        collection.update({"id" : busi['id']}, { '$set' : { 'reviews': [] } })
        npages = get_npages(busi['url'])
    
        for page in xrange(npages):

            index = page * 40
            if page == 0:
                url = '%s' % busi['url']
            else:
                url = '%s?start=%d' % (busi['url'], index)
            text = try_requests(url)

            if len(text) > 0:
                soup = BeautifulSoup(text, "html.parser")
                rev.extend(soup.find_all('div', class_ = 'review'))
            
                #collection.update({"id" : busi['id']}, { '$push' : { 'reviews': { '$each': [ { 'html' : str(item) } for item in rev ]}}})
            time.sleep(1)
        try:
            collection.update({"id" : busi['id']}, { '$set' : { 'reviews': [ { 'html' : str(item) } for item in rev ]} })
        except:
            with open("failed.txt", "w") as f:
                f.write(rev)
        

def parse_reviews(busi, collection):
    print "getting stars for " + busi['name']

    business = collection.find_one({"id" : busi['id'] })
    for review in business['reviews']:
        soup = BeautifulSoup(review['html'], "html.parser")
 
        if soup.find(itemprop = "reviewRating"):
            review['rating'] = soup.find(itemprop = "ratingValue")['content']
            #collection.save(business)
            
if __name__ == '__main__':
    for busi in coll.find({'name': 'The House'}):
        get_reviews(busi, coll)
    # count = 0
    # for busi in coll.find():
    #     print 'restaurant: ', count
    #     get_reviews(busi, coll)
    #     count += 1

    #     parse_reviews(busi, coll)
    #     # five_stars = filter(lambda x: x['rating'] == '5.0', coll.find_one({"id" : busi['id']})['reviews'])