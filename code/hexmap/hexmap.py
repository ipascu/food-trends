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

app = Flask(__name__)

def run_on_start():
    print 'loading the model'
    f = open('static/data/model_small.pkl')
    return pkl.load(f)

def query_term(term):
    return app.model.query(term)

def df_to_listofdict(df):
    return [row[1].to_dict() for row in df.iterrows()]

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/results', methods=['POST', 'GET'])
def results():
    search_term = request.form['search_term']
    print search_term
    data = query_term(search_term)
    data = data[(data['lati'] != 999) & (data['longi'] != 999)]
    data.to_csv('static/data/%s.csv' % search_term, index=False)
    file_path = url_for('static', filename='data/%s.csv' % search_term)
    return render_template('results.html', file_path=file_path)

if __name__ == '__main__':
    app.model = run_on_start()
    app.run(port=7070)
