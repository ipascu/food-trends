from pymongo import MongoClient
from pymongo import errors
from bs4 import BeautifulSoup
import requests
import sys
import logging
import time
import pdb

client = MongoClient()
db = client.yelp
coll = db.restaurant

auth = requests.auth.HTTPProxyAuth('username', 'password')
proxies = {'http': 'http://us.proxymesh.com:31280'}


def get_npages(url):
    '''
    extract the number of pages of reviews to loop through
    '''
    text = try_requests(url)
    if len(text) > 0:
        soup = BeautifulSoup(text, "html.parser")
        pages = soup.find('div', class_="page-of-pages").text.split()[-1]
        return int(pages)
    return 0

def get_curr_rev_cnt(busi):
    ''' 
    how many reviews have we scraped for this business so far 
    '''
    return len(busi.get('reviews',[]))

def try_requests(url):
    '''
    catch url request errors and re-try 3 times with 5 second pause
    '''
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
            logging.warning('Could not access link %s' % url)
            return ""
    except:
        logging.warning('Could not access link %s' % url)
        return ""


def get_reviews(busi, collection):
    logging.warning("getting reviews for " + busi['name'])
           
    if get_curr_rev_cnt(busi) < min(1600, busi.get('review_count', 0))
        and busi.get('review_count', 0) > 0:
        
        rev = []
	
        collection.update({"id" : busi['id']}, { '$set' : { 'reviews': [] } })
        npages = get_npages(busi['url'])
    
        pagen = min(40,npages)
        for page in xrange(pagen):

            index = page * 40
            if page == 0:
                url = '%s' % busi['url']
            else:
                url = '%s?start=%d' % (busi['url'], index)
            text = try_requests(url)

            if len(text) > 0:
                soup = BeautifulSoup(text, "html.parser")
                rev.extend(soup.find_all('div', class_ = 'review'))
            
            time.sleep(0.25)
        try:
            collection.update({"id" : busi['id']}, { '$set' : { 'reviews': [ { 'html' : str(item) } for item in rev ]} })
        except:
            with open("failed.txt", "w") as failed:
                for item in rev:
                  failed.write("%s\n" % item)        

def parse_reviews(busi, collection):
    print "getting stars for " + busi['name']

    business = collection.find_one({"id" : busi['id'] })
    for review in business['reviews']:
        soup = BeautifulSoup(review['html'], "html.parser")
 
        if soup.find(itemprop = "reviewRating"):
            review['rating'] = soup.find(itemprop = "ratingValue")['content']
            #collection.save(business)
            
if __name__ == '__main__':
    count = 0
    # find the restaurants with no reviews scraped or an empty list of reviews
    item_lst = list(coll.find({ "$or": [{ "reviews" : {"$exists" :0}}, {"reviews": {"$size":0}}]}).sort('_id'))
    print len(item_lst)
   
    start = int(sys.argv[1])
    end = int(sys.argv[2])
    name = "log_%d_%d.txt" % (start, end)	
    logging.basicConfig(filename=name, level=logging.WARNING)

    sublst = item_lst[start:end]
    for busi in sublst:
	time.sleep(1)
	start = time.time()
        logging.warning('restaurant: %d ' % count)
        get_reviews(busi, coll)
        count += 1
	end = time.time()
	logging.warning("took %d seconds" % (end-start))
    
    logging.warning("DONE")
    #     parse_reviews(busi, coll)
    #     # five_stars = filter(lambda x: x['rating'] == '5.0', coll.find_one({"id" : busi['id']})['reviews'])
