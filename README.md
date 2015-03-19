## Explore San Francisco Restaurant Reviews

#### Iuliana Pascu, March 2015

### Overview

The app is live at [Word2Maps](http://www.word2maps.com Word2Maps).  

The idea of this project is to allow a user, or data scientist, to explore and learn about a city from the text of Yelp restaurant reviews. My goal was to structure this data and help users extract insights about the local restaurant market. The user can use the search app to run their own queries and learn about San Francisco.

### Examples

The maps are built using terms extracted from San Francisco Yelp restaurant reviews from December 2014. The size of the hexagons is proportional to the number of reviews in the area and gives a representation of the density of restaurant activity. The colors indicate the share of the reviews in that cell that contain the search term or words related to it.

RED is a higher share of reviews containing the relevant terms.  
SIZE is the total number of reviews and does not change between searches.

##### Example query: hipster
![Alt text](/examples/hipster.jpg)


### How it works

I trained word2vec using text from approximately 1.5 million Yelp restaurant reviews in San Francisco. This includes the entire history of Yelp restaurant reviews starting in 2004, for 7230 restaurants in the area. Word2vec embeds words into a vector space by trying to predict the context of a word. Words that show up in similar contexts will tend to map into similar vectors.

Building on this, I use nearest neighbors based on cosine similarity to generate terms related to the search query and use this to extract information about the topic of interest from reviews.

For example, searching for "spaghetti" extracts the following terms: "basilica", "bolognese", "pescatora", "penne", "linguini", "carbonara", etc. which helps a user learn about Italian cuisine and where it is located in the San Francisco restaurant scene.

Searching for "dirty" extracts the following terms: "dusty", "unclean", "filthy", "grimy".

Reviews were transformed into a matrix of word counts that is filtered according to the search terms. This process is fast and allows for a good user experience when interacting with the website. The results are aggregated using [hexbin](http://www.delimited.io/blog/2013/12/1/hexbins-with-d3-and-leaflet-maps) maps.

The maps display only reviews from December 2014 for faster rendering. 

##### Caveats:  
Because adjectives with opposite meaning show up in similar contexts the model can sometimes pull both of them as a similar topic. Example: a search for "small" will pull "large", "small-ish", "dinky" and "tiny" as related terms. Training on a larger training set can fix some of these problems. Right now this is a tool for also understanding how word2vec works for this body of text.

### Project Pipeline
1. Yelp API -> MongoDB (metadata)  
2. Yelp review scraping -> MongoDB
3. MongoDB -> PostgreSQL
- word2vec (gensim) trained on 1.5 million reviews
- sklearn CountVectorizer to transform the reviews to be used for plots
- construct related word groups based on cosine similarity
- hexbin map

#### Future Steps
I think this project has a lot of future potential for development. A few directions that would be fun to explore are:
2. Visualize changes in the maps over time -- can we create a visualization of the major transformations San Francisco has gone through with the information extracted from these reviews?
- Add information about the restaurants with a high number of reviews matching the search term in the search page -- the model can extract information about cases of food poisoning, health department violations, etc.
1. Retrain the model allowing for bi-grams and with a larger training set.
- Explore how word similarities differ when the model is trained with New York vs. San Francisco data.

#### Packages used
- psycopg2
- pymongo
- sklearn
- nltk
- gensim
- numpy
- pandas

### Background Resources
- [word2vec](https://code.google.com/p/word2vec/)
- [hexbin maps](http://www.delimited.io/blog/2013/12/1/hexbins-with-d3-and-leaflet-maps)
- [Yelp API](https://www.yelp.com/developers/documentation)
