#!/usr/bin/env python
import sys
from flask import Flask
from flask import render_template

import config

c = config.Config()

sys.path.append(c.get('backend','opengrid'))
from library import houseprint

app = Flask(__name__)

import cache_anonymous_houseprint as cah
cah.cache()
hp = houseprint.load_houseprint_from_file('hp_anonymous.pkl')

@app.route("/")
def index():
    return render_template('index.html', fluksos=hp.fluksosensors.keys())

@app.route("/flukso/<fluksoid>")
def flukso(fluksoid):
    return render_template('flukso.html', 
    	#flukso=hp.fluksosensors[fluksoid]
    	flukso=fluksoid)

if __name__ == "__main__":
    app.run(debug=False,host='0.0.0.0',port=5000)
    #app.run(debug=True)