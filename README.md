##Mapping food topics in San Francisco

#### Iuliana Pascu, March 2015

### Overview
Website is live at word2maps.com.

### Dataset
The word2vec model for this project was trained on 1.5 million Yelp restaurant reviews from San Francisco. This includes the entire history of reviews, ### restaurants.

The maps were created using reviews from 12/01/2014 - 12/31/2014.

### Modeling
#### Word2Vec
#### CountVectorizer
#### Hexbin Maps

### Analysis Choices and Details


### Examples


### Next Steps

#### Add the time dimension
#### Include bi-grams in the model
#### 



Work in progress for capstone project.

Code done so far:

Yelp data collection - calls to the API for the meta data, scraping reviews from webpages.
MongoDB review data cleaning. Mongo -> SQL restructuring of reviews.

Foursquare API menu data collection - calls to the API for restaurant meta data, using the venueId from foursquare to collect menu data.
Creating a corpus from the menu information and NMF on this corpus to construct food topics.

Query to construct SQL time-series.

