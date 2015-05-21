#!/usr/bin/env python
import sys
from collections import namedtuple
from flask import Flask
from flask import render_template

from arrow import Arrow
from nvd3 import lineWithFocusChart

import config

c = config.Config()

sys.path.append(c.get('backend','opengrid'))
from library import houseprint, fluksoapi

app = Flask(__name__)

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
    path_to_csv = c.get('data','folder')
    start = Arrow.now().floor('day').replace(days=-7).datetime
    end = Arrow.now().floor('day').datetime
    df = fluksoapi.load(path_to_csv, [sensorid], start=start, end=end).fillna(0)
    
    if len(df.columns):
        #Prepare chart name and epoch timescale
        chart_name = "measured usage"
        df["epoch"] = [(Arrow.fromdatetime(o) - Arrow(1970, 1, 1)).total_seconds()*1000 for o in df.index]
        
        #Create NVD3 chart
        chart = lineWithFocusChart(x_is_date=True,name=chart_name,height=450,width=800)
        series_name = "{}".format(hp.get_flukso_from_sensor(sensorid))
        chart.add_serie(name=series_name, x=list(df["epoch"]), y=list(df[sensorid]))
        
        #Get chart HTML code
        chart.buildhtmlheader()
        chart.buildcontent()
        chartheader = chart.htmlheader
        chartcontent = chart.htmlcontent
    else:
        chartheader = ''
        chartcontent = '<div>No Data</div>'
    
    return render_template('sensor.html',
      sensorid=sensorid,
      chartheader = chartheader,
      chartcontent = chartcontent)

if __name__ == "__main__":
    app.run(debug=False,host='0.0.0.0',port=5000)
    #app.run(debug=True)