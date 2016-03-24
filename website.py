#!/usr/bin/env python
import sys
import os
import pandas as pd
import config
from flask import Flask, render_template, send_file, flash, redirect, url_for, safe_join, request, abort, session
from forms import SearchForm, DownloadForm, EmptyForm
import plot
import gc
from flask_dance.contrib.github import make_github_blueprint, github
from functools import wraps

c = config.Config()

try:
    from opengrid.library import houseprint
except ImportError:
    sys.path.append(c.get('backend', 'opengrid'))
    from opengrid.library import houseprint

if not os.path.exists("static/sandbox"):
    os.mkdir("static/sandbox")
if not os.path.exists("static/downloads"):
    os.mkdir("static/downloads")

app = Flask(__name__)
SECRET_KEY = "secret_key"  # TODO add a real key in the config file
app.config.from_object(__name__)

blueprint = make_github_blueprint(
    client_id=c.get('github','clientid'),
    client_secret=c.get('github','clientsecret'),
)
app.register_blueprint(blueprint, url_prefix="/login")

try:
    hp = houseprint.Houseprint()
except:
    print("Connection failed, loading houseprint from cache")
    hp = houseprint.load_houseprint_from_file("cache_hp.hp")
else:
    hp.save("cache_hp.hp")

hp.init_tmpo()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not github.authorized:
            abort(401)
        return f(*args, **kwargs)
    return decorated_function


def contributor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'contributor' not in session or session['contributor'] == False:
            flash('You need to be a contributor to the OpenGrid project to view this page!')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
@app.route("/index")
def index():
    return render_template('index.html')


@app.route("/login")
def login():
    if not github.authorized:
        return redirect(url_for("github.login"))

    user = github.get("/user").json()
    repos = github.get(user['repos_url']).json()

    # if you have opengrid in your repositories, you are a contributor :-)
    session['contributor'] = 'opengrid' in {repo['name'] for repo in repos}
    session['username'] = user["login"]

    return redirect(url_for('index'))


@app.route("/data")
def data():
    devices = hp.get_devices()
    devices.sort(key=lambda x: x.key)
    return render_template('data.html', fluksos=devices)


@app.route("/development")
def development():
    return render_template('development.html')


@app.route("/sandbox/")
@app.route("/sandbox/<filename>")
@login_required
def manualresults(filename=None):
    #  path = c.get('backend', 'sandbox')
    path = "static/sandbox"
    if filename is None:
        resultfiles = os.listdir(path)
        notebooks = [plot.Notebook(title=resultfile, path=path) for resultfile in resultfiles]
        return render_template('sandbox.html', files=notebooks)
    else:
        file_path = safe_join(path, filename)
        return send_file(file_path)


@app.route("/flukso/<fluksoid>")
def flukso(fluksoid):
    f = hp.find_device(fluksoid)

    if f is None:
        abort(404)

    sensors = f.get_sensors()
    sensors.sort(key=lambda x: x.type)

    return render_template(
        'flukso.html',
        flukso=f,
        sensors=sensors
    )


@app.route("/sensor/<sensorid>")
def sensor(sensorid):
    s = hp.find_sensor(sensorid)

    if s is None:
        abort(404)

    path = c.get('backend', 'figures')

    analyses = []
    units = dict(electricity="Watt",
                 gas="Watt",
                 water="liter/min")

    # create timeseries plot
    filename = 'TimeSeries_{}.html'.format(s.key)
    analyses.append(
        plot.Html(
            title='Timeseries',
            content=safe_join(path, filename),
            description=u"This interactive graph  shows the measurement of {sensordescription} over the last 7 days.\
                                 The unit of the data is {unit}, and the graph contains minute values.\
                                 The graph is interactive: use the bottom ruler to zoom in/out and to change the period. \
                                 The graph is in local time (for Belgium).".format(sensordescription=s.description,
                                                                                   unit=units.get(s.type))
        )
    )

    if s.type == 'electricity' and not s.system == 'solar':
        # create standby horizontal
        filename = 'standby_horizontal_{}.png'.format(s.key)
        analyses.append(
            plot.Figure(
                title='Standby 10 days',
                content=filename,
                description=u"This figure shows the electric standby power of {sensordescription} (in {unit}). \
                             The left plot shows your standby power over the last 10 days (red diamonds). The distribution\
                             of the standby power of other opengrid families is shown as a boxplot. The red line is the median,\
                             the box limits are the 25th and 75th percentiles. By comparing your standby power to this box,\
                             you get an idea of your position in the opengrid community.\
                             The right plot shows your measured power consumption of {sensordescription} for the last night.\
                             This may give you an idea of what's going on in the night. Try to switch something off tonight and\
                             come back tomorrow to this graph to see the effect!".format(
                    sensordescription=s.description,
                    unit=units.get(s.type))
            )
        )
        # create standby vertical
        filename = 'standby_vertical_{}.png'.format(s.key)
        analyses.append(
            plot.Figure(
                title='Standby 40 days',
                content=filename,
                description=u"This figure also shows the electric standby power of {sensordescription} (in {unit}). \
                             The left plot shows your standby power over the last 40 days (red diamonds).\
                             The standby power of other opengrid families is indicated by the 10th, 50th and 90th percentile.\
                             Again, this allows you to get an idea of your standby power in comparison to the opengrid community.\
                             The right plot shows your measured power consumption of {sensordescription} for the last night.\
                             This may give you an idea of what's going on in the night. Try to switch something off tonight and\
                             come back tomorrow to this graph to see the effect!<br><br>\
                             Which of these two graphs do you prefer? Let us know in the\
                             <a href=\"https://groups.google.com/d/forum/opengrid-private\">forum</a>.".format(
                    sensordescription=s.description,
                    unit=units.get(s.type))
            )
        )

    # create carpet plot
    filename = 'carpet_{}_{}.png'.format(s.type, s.key)
    analyses.append(
        plot.Figure(
            title='Carpet plot',
            content=filename,
            description=u"This plot shows the measurement of {sensordescription} over the last 3 weeks in a 'raster'. \
                         Each day is a single row in the 'raster', the horizontal axis is time (0-24h).\
                         The intensity of the measurement is plotted as a color: blue is low, red is high.  <br><br> \
                         The plot shows when the consumption typically takes place. \
                         This is useful discover trends or patterns over a day or week.\
                         This allows to check if systems are correctly scheduled (night set-back for heating, clock for\
                         an electrical boiler, etc. )<br><br>\
                         Do you think this is useful? Let us know in the\
                         <a href=\"https://groups.google.com/d/forum/opengrid-private\">forum</a>.".format(
                sensordescription=s.description)
        )
    )

    analyses = [analysis for analysis in analyses if analysis.has_content()]

    return render_template(
        'sensor.html',
        sensor=s,
        analyses=analyses
    )


@app.route("/figures/<filename>")
def figure(filename):
    path = c.get('backend', 'figures')
    file_path = safe_join(path, filename)

    return send_file(file_path)


def figure_exists(filename):
    path = c.get('backend', 'figures')
    file_path = safe_join(path, filename)

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
                df = s.get_data(
                    head=pd.Timestamp(form.start.data),
                    tail=pd.Timestamp(form.end.data),
                    resample=form.resample.data
                )
            except:
                flash("Error connecting to the data storage, please try again later")
            else:
                filename = '{}.csv'.format(s.key)
                filepath = safe_join("static/downloads", filename)
                df.to_csv(filepath, encoding='utf-8')
                del df
                gc.collect()
                return send_file(
                    filepath,
                    as_attachment=True
                )

    if guid is not None:
        form.guid.data = guid

    return render_template(
        'download.html',
        form=form
    )


@app.route("/issue30", methods=['GET', 'POST'])
@login_required
@contributor_required
def issue30():
    form = EmptyForm()  # Empty form, only validates the secret token to protect against cross-site scripting

    if request.method == 'POST' and form.validate():
        if request.form['submit'] == 'Sync TMPO':
            try:
                hp.sync_tmpos()
            except:
                flash("Error syncing TMPO, please try again later")
            else:
                flash("TMPO Sync Successful")
        elif request.form['submit'] == 'Reset Houseprint':
            hp.reset()
            flash("Houseprint Reset Successful")

    return render_template(
        'issue30.html',
        form=form
    )


@app.errorhandler(401)
def internal_error(error):
    flash('ERROR 401 - Not Authorized')
    return redirect(url_for('index'))


@app.errorhandler(403)
def internal_error(error):
    flash('ERROR 403 - Forbidden')
    return redirect(url_for('index'))


@app.errorhandler(404)
def internal_error(error):
    flash('ERROR 404 - Page not found')
    return redirect(url_for('index'))


if __name__ == "__main__":
    try:
        env = c.get('env', 'type')
    except:
        env = 'prod'

    if env == 'dev':
        context = ('key.crt', 'key.key')
        app.run(debug=True, ssl_context=context)
    else:
        app.run(debug=False, host='0.0.0.0', port=5000)
