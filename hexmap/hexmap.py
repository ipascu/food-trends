from flask import Flask
from flask import render_template
from flask import url_for
from flask import request
import pandas as pd
import json
from gensim_cluster import ReviewModel
import cPickle as pkl
import time
import sys
import dill

app = Flask(__name__)

def run_on_start():
    print 'loading the model'
    f = open('static/data/model_aws.pkl')
    return dill.load(f)

def query_term(term):
    return app.model.query(term)

def cluster(term):
    return app.model.closest_words(term)

def df_to_listofdict(df):
    return [row[1].to_dict() for row in df.iterrows()]

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/results', methods=['POST', 'GET'])
def results():
    search_term = request.form['search_term'].lower()
    print search_term
    data = query_term(search_term)
    words = cluster(search_term)

    data = data[(data['lati'] != 999) & (data['longi'] != 999)]
    data.to_csv('static/data/%s.csv' % search_term, index=False)
    mean = data['flag'].mean()
    print 'average value', mean
    file_path = url_for('static', filename='data/%s.csv' % search_term)
    return render_template('results.html', file_path=file_path, mean_val=mean, words=words)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error_page.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error_page.html'), 500

if __name__ == '__main__':
    app.model = run_on_start()
    app.run(port=80, host='0.0.0.0')
