#!/usr/bin/env python
import sys, os
from collections import namedtuple
from flask import Flask, render_template, send_file, flash, redirect, url_for, safe_join, request

import config

c = config.Config()

sys.path.append(c.get('backend','opengrid'))
from opengrid.library import houseprint

app = Flask(__name__)
SECRET_KEY = "secret_key"  # TODO add a real key in the config file
app.config.from_object(__name__)

hp = houseprint.Houseprint()


@app.route("/")
def index():
    return render_template('index.html', fluksos=hp.get_devices())


@app.route("/flukso/<fluksoid>")
def flukso(fluksoid):
    f = hp.find_device(fluksoid)

    return render_template(
            'flukso.html',
            flukso=f,
            sensors=f.get_sensors()
    )


@app.route("/sensor/<sensorid>")
def sensor(sensorid):

    s = hp.find_sensor(sensorid)

    analyses = ['timeseries']
    if s.type == 'electricity' and not s.system == 'solar':
        analyses.append('standby_horizontal')
        analyses.append('standby_vertical')
    
    return render_template(
            'sensor.html',
            sensor=s,
            analyses=analyses
    )


@app.route("/standby_horizontal/<sensorid>")
def standby_horizontal(sensorid):

    s = hp.find_sensor(sensorid)

    filename = 'standby_horizontal_'+sensorid+'.png'

    if not figure_exists(filename):
        flash('No standby_horizontal graph found for this sensor')
        return redirect(url_for('sensor', sensorid=sensorid))

    return render_template(
            'analysis_image.html',
            analysisname='Standby Horizontal',
            filename=filename,
            sensor=s
    )


@app.route("/standby_vertical/<sensorid>")
def standby_vertical(sensorid):

    s = hp.find_sensor(sensorid)

    filename = 'standby_vertical_{}.png'.format(s.key)

    if not figure_exists(filename):
        flash('No standby_vertical graph found for this sensor')
        return redirect(url_for('sensor', sensorid=sensorid))

    return render_template(
            'analysis_image.html',
            analysisname = 'Standby Vertical',
            filename = filename,
            sensor = s)


@app.route("/timeseries/<sensorid>")
def timeseries(sensorid):

    s = hp.find_sensor(sensorid)

    path = c.get('backend','figures')
    filename = 'TimeSeries_{}.html'.format(s.key)
    file_path = safe_join(path,filename)

    if not os.path.exists(file_path):
        flash('No timeseries graph found for this sensor')
        return redirect(url_for('sensor', sensorid=sensorid))

    with open (file_path, "r") as html_graph:
        content = html_graph.read()

    return render_template(
            'analysis_html.html',
            analysisname='Time Series',
            sensor=s,
            content=content
    )


@app.route("/figures/<filename>")
def figure(filename):
    path = c.get('backend','figures')
    file_path = safe_join(path,filename)

    return send_file(file_path)


def figure_exists(filename):
    path = c.get('backend','figures')
    file_path = safe_join(path,filename)

    return os.path.exists(file_path)

if __name__ == "__main__":
    app.run(debug=False,host='0.0.0.0',port=5000) #TODO: implement switch between development and production mode in config file
    #app.run(debug=True)