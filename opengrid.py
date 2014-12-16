#!/usr/bin/env python
from flask import Flask
from flask import render_template
from opengrid.library import houseprint
app = Flask(__name__)

hp = houseprint.load_houseprint_from_file('hp_anonymous.pkl')

@app.route("/")
def index():
    return render_template('index.html', fluksos=hp.fluksosensors.keys())

@app.route("/flukso/<fluksoid>")
def flukso(fluksoid):
    return render_template('flukso.html', flukso=hp.fluksosensors[fluksoid])

if __name__ == "__main__":
    app.run(debug=True)
