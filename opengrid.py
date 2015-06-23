#!/usr/bin/env python
import sys, os
from collections import namedtuple
from flask import Flask, render_template, send_file, flash, redirect, url_for, safe_join, request

import config

c = config.Config()

sys.path.append(c.get('backend','opengrid'))
from library import houseprint, fluksoapi

app = Flask(__name__)
SECRET_KEY = "secret_key" #TODO add a real key in the config file
app.config.from_object(__name__)

import cache_anonymous_houseprint as cah
cah.cache()
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

@app.route("/standby_horizontal/<sensorid>")
def standby_horizontal(sensorid):

    filename = 'standby_horizontal_'+sensorid+'.png'

    if not figure_exists(filename):
        flash('No standby_horizontal graph found for this sensor')
        return redirect(url_for('sensor', sensorid=sensorid))

    return render_template('analysis_image.html',
        analysisname = 'Standby Horizontal',
        filename = filename,
        sensorid = sensorid)

@app.route("/standby_vertical/<sensorid>")
def standby_vertical(sensorid):

    filename = 'standby_vertical_'+sensorid+'.png'

    if not figure_exists(filename):
        flash('No standby_vertical graph found for this sensor')
        return redirect(url_for('sensor', sensorid=sensorid))

    return render_template('analysis_image.html',
        analysisname = 'Standby Vertical',
        filename = filename,
        sensorid = sensorid)

@app.route("/timeseries/<sensorid>")
def timeseries(sensorid):

    path = c.get('backend','figures')
    filename = 'TimeSeries_'+sensorid+'.html'
    file = safe_join(path,filename)

    if not os.path.exists(file):
        flash('No timeseries graph found for this sensor')
        return redirect(url_for('sensor', sensorid=sensorid))

    with open (file, "r") as myfile:
        content = myfile.read()

    return render_template('analysis_html.html',
        analysisname = 'Time Series',
        sensorid = sensorid,
        content = content)

@app.route("/figures/<filename>")
def figure(filename):
    path = c.get('backend','figures')
    file = safe_join(path,filename)

    return send_file(file)

def figure_exists(filename):
    path = c.get('backend','figures')
    file = safe_join(path,filename)

    return os.path.exists(file)

if __name__ == "__main__":
    app.run(debug=False,host='0.0.0.0',port=5000) #TODO: implement switch between development and production mode in config file
    #app.run(debug=True)