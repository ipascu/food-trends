# yelp scraping data from Jeff
# http://jyt109.github.io/posts/yelp-rest-scrape.html

# A simple example of how to scrape reviews from yelp
# and put it in a MongoDB database

# This assumes you already have scrape the metadata 
# using the yelp API

import json
import requests
import bs4
import pymongo

client = pymongo.MongoClient()
db = client['yelp2']

db.create_collection('info')

yelp = json.load(open('data/yelp.json'))

yelp[0].keys()
'''
[u'is_claimed',
 u'rating',
 u'mobile_url',
 u'rating_img_url',
 u'review_count',
 u'name',
 u'rating_img_url_small',
 u'url',
 u'snippet_text',
 u'image_url',
 u'is_closed',
 u'rating_img_url_large',
 u'_id',
 u'id',
 u'categories',
 u'location']
'''

for entry in yelp:
    link = entry['url']
    response = requests.get(link).content
    soup = bs4.BeautifulSoup(response)
    reviews = soup.select('.review_comment.ieSucks')
    reviews_txt = [review.text.strip() for review in reviews]
    entry['review_txt'] = reviews_txt
    num_stars5 = len(soup.select('.star-img.stars_5'))
    entry['num_5_star'] = num_stars5
    entry['_id'] = entry['_id']['$oid']
    db.info.insert(entry)

list(db.info.find({}, {'num_5_star':1}))

