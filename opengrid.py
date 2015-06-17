#!/usr/bin/env python
import sys, os
from collections import namedtuple
from flask import Flask, render_template, send_file, flash, redirect, url_for

import config

c = config.Config()

sys.path.append(c.get('backend','opengrid'))
from library import houseprint, fluksoapi

app = Flask(__name__)
SECRET_KEY = "secret_key"
app.config.from_object(__name__)

import cache_anonymous_houseprint as cah
#cah.cache()
hp = houseprint.load_houseprint_from_file('hp_anonymous.pkl')

@app.route("/")
def index():
    return render_template('index.html', fluksos=hp.fluksosensors.keys())

@app.route("/flukso/<fluksoid>")
def flukso(fluksoid):
    Sensor = namedtuple('Sensor', 'id, type')
    return render_template('flukso.html', 
      flukso=fluksoid,
      sensors = [Sensor(id=s['Sensor'], type=s['Type']) for s in hp.fluksosensors[fluksoid].values() if s])

@app.route("/sensor/<sensorid>")
def sensor(sensorid):

    analyses = ['standby_horizontal','standby_vertical','timeseries']
    
    return render_template('sensor.html',
      sensorid=sensorid,
      analyses=analyses
      )

@app.route("/standby_horizontal/<sensorid>.png")
def standby_horizontal(sensorid):
    path = c.get('backend','figures')
    filename = path + '/standby_horizontal_'+sensorid+'.png'

    if not os.path.exists(filename):
        flash('No standby_horizontal graph found for this sensor')
        return redirect(url_for('sensor', sensorid=sensorid))

    return send_file(filename, mimetype='image/png')

@app.route("/standby_vertical/<sensorid>.png")
def standby_vertical(sensorid):

    path = c.get('backend','figures')
    filename = path + '/standby_vertical_'+sensorid+'.png'

    if not os.path.exists(filename):
        flash('No standby_vertical graph found for this sensor')
        return redirect(url_for('sensor', sensorid=sensorid))

    return send_file(filename, mimetype='image/png')

@app.route("/timeseries/<sensorid>.html")
def timeseries(sensorid):
    path = c.get('backend','figures')
    filename = path + '/TimeSeries_'+sensorid+'.html'

    if not os.path.exists(filename):
        flash('No timeseries graph found for this sensor')
        return redirect(url_for('sensor', sensorid=sensorid))

    return send_file(filename, mimetype='text/html')

if __name__ == "__main__":
    #app.run(debug=False,host='0.0.0.0',port=5000)
    app.run(debug=True)