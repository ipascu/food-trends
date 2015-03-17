## Explore San Francisco Restaurant Reviews

#### Iuliana Pascu, March 2015

### Overview

The app is live at [Word2Maps](http://www.word2maps.com Word2Maps).  

The idea of this project is to allow a user, or data scientist, to explore and learn about a city from the text of restaurant reviews. My goal was to build stories around this data and explore trends and changes in the market. The user can use the search engine to run their own queries and learn about San Francisco.

### Examples

The maps use Yelp restaurant reviews from December 2014 to build the metrics. The size of the hexagons is proportional to the number of reviews in the area. The colors indicate the share of the reviews in that cell that contain the search term or words related to it.

Just from the size and density of the hexagon one can easily see where the clusters of activity are in San Francisco.


##### Example query: view
![Alt text](/examples/view2.jpg)


### Dataset
The word2vec model for this project was trained on approximately 1.5 million Yelp restaurant reviews from San Francisco. This includes the entire history of reviews starting in 2004, 7230 restaurants in the area.

The maps were created using reviews from 12/01/2014 - 12/31/2014.

### Modeling
#### Word2Vec
#### CountVectorizer
#### Hexbin Maps


### Project Pipeline

Yelp Data collections
Use calls to the Yelp API to collect restaurant meta data for approximately 8000 restaurants in the San Francisco area. Store the data in MongoDB.

Using restaurant urls scrape restaurant reviews.

Rebuild the database in SQL in a time-series format. Relations in the database are:

Train word2vec model on the restaurant reviews using the gensim package.

Parse one month of reviews, build word counts.

### Next Steps

#### Add the time dimension
#### Include bi-grams in the model
####
