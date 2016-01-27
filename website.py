#!/usr/bin/env python
import sys
import os
import pandas as pd
import config
from flask import Flask, render_template, send_file, flash, redirect, url_for, safe_join, request
from forms import SearchForm, DownloadForm
if sys.version_info.major >= 3:
    from io import StringIO
else:
    from StringIO import StringIO

c = config.Config()

sys.path.append(c.get('backend','opengrid'))
from opengrid.library import houseprint

app = Flask(__name__)
SECRET_KEY = "secret_key"  # TODO add a real key in the config file
app.config.from_object(__name__)

try:
    hp = houseprint.Houseprint()
except:
    print("Connection failed, loading houseprint from cache")
    hp = houseprint.load_houseprint_from_file("cache_hp.hp")
else:
    hp.save("cache_hp.hp")


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/data")
def data():
    return render_template('data.html', fluksos=hp.get_devices())


@app.route("/development")
def development():
    return render_template('development.html')


@app.route("/subscribe")
def subscribe():
    return render_template('subscribe.html')


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


@app.route("/search", methods=['GET', 'POST'])
def search():

    form = SearchForm()
    if request.method == 'POST' and form.validate():
        f = hp.find_device(form.search_string.data)
        if f is not None:  # flukso was found
            return redirect(url_for('flukso', fluksoid=f.key))
        else:
            flash("Sorry, we couldn't find that Fluksometer")

    return render_template(
            "search.html",
            form=form)


@app.route("/download", methods=['GET', 'POST'])
@app.route("/download/<guid>")
def download(guid=None):
    form = DownloadForm()

    if request.method == 'POST' and form.validate():
        s = hp.find_device(form.guid.data)
        if s is None:
            s = hp.find_sensor(form.guid.data)

        if s is None:
            flash("ID not found")
        else:
            try:
                # We need to connect and disconnect with tmpo
                # to make sure the website doesn't lock access to the sqlite
                hp.init_tmpo()
                tmpos = hp.get_tmpos()
                output = StringIO()
                df = s.get_data(
                        head=pd.Timestamp(form.start.data),
                        tail=pd.Timestamp(form.end.data),
                        resample=form.resample.data
                )
                tmpos.dbcon.close()
            except:
                # This will happen if another process is currently using the tmpo
                flash("Error connecting to the data storage, please try again later")
            else:
                df.to_csv(output, encoding='utf-8')
                output.seek(0)
                return send_file(
                        output,
                        mimetype="text/csv",
                        as_attachment=True,
                        attachment_filename='{}.csv'.format(s.key)
                )
    if guid is not None:
        form.guid.data = guid

    return render_template(
            'download.html',
            form=form
    )

if __name__ == "__main__":
    try:
        env = c.get('env','type')
    except:
        env = 'prod'

    if env == 'dev':
        app.run(debug=True)
    else:
        app.run(debug=False,host='0.0.0.0',port=5000)