import os
import pandas as pd
import gc
import sys
import json

from flask_dance.contrib.github import github
from flask import render_template, flash, redirect, url_for, session, \
    request, safe_join, send_file, abort, Response
from werkzeug.utils import secure_filename

from flask_app import app, env, hp, c, sandbox_path, download_path, slackbot
from .wrappers import user_is_contributor, login_required, contributor_required
from .forms import SearchForm, DownloadForm, DownloadRegressionForm, EmptyForm, Recalculate
import plot


sys.path.append("/usr/local/opengrid")
from opengrid.recipes import mvreg_sensor


@app.route("/")
@app.route("/index")
def index():
    return render_template('index.html')


@app.route("/login")
def login():
    if env == 'dev':
        flash('You are in dev mode, and don\'t need to login')
        return redirect(url_for('index'))

    if not github.authorized:
        return redirect(url_for("github.login"))

    user = github.get("/user").json()
    orgs = github.get(user['organizations_url']).json()

    # if you have opengridcc in your public organizations, you are a contributor :-)
    session['contributor'] = 'opengridcc' in {org['login'] for org in orgs}
    session['username'] = user["login"]

    if user_is_contributor():
        flash('Welcome, {user}. Thanks for contributing to OpenGrid!'.format(user=session['username']))
    else:
        flash('Welcome, {user}. Become an OpenGrid member to view all restricted pages\n'
              'To register yourself as OpenGrid member, send a mail to roeldeconinck@gmail.com'.format(
            user=session['username']))

    return redirect(url_for('index'))


@app.route("/logout")
def logout():
    if env == 'dev':
        flash('You are in dev mode, no need to logout')
        return redirect(url_for('index'))
    session.pop('username', None)
    session.pop('contributor', None)

    flash('Logout successful')
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
@app.route("/sandbox/file/<filename>")
@app.route("/sandbox/upload", methods=['POST'])
@app.route("/sandbox/delete", methods=['POST'])
@login_required
@contributor_required
def sandbox(filename=None):
    #  path = c.get('backend', 'sandbox')
    path = sandbox_path

    #  Upload file
    if request.method == 'POST' and 'upload' in request.url_rule.rule:
        file = request.files['file']
        if file.filename == '':
            flash('Select a valid file to upload')
        elif get_extension(file.filename) not in {'jpg', 'jpeg', 'gif', 'png', 'pdf', 'html', 'json'}:
            flash('File type not allowed, only images, pdf\'s, html or json')
        else:
            file_name = secure_filename(file.filename)
            if file_name in os.listdir(path):
                flash('Upload failed: file name "{}" already taken.\
                Please change file name and try again.'.format(file_name))
            else:
                file_path = os.path.join(path, file_name)
                file.save(file_path)
                flash('Upload successful')

    #  Request of specific file
    if request.method == 'GET' and filename is not None:
        file_path = safe_join(path, filename)
        # send json as attachment
        as_attachment = get_extension(filename) in {'json'}
        return send_file(file_path, as_attachment=as_attachment)

    #  Delete file
    if request.method == 'POST' and 'delete' in request.url_rule.rule:
        filename = request.form['filename']
        file_path = safe_join(path, filename)
        os.remove(file_path)
        flash('{filename} deleted'.format(filename=filename))

    #  Normal behaviour
    resultfiles = os.listdir(path)
    notebooks = [plot.Notebook(title=resultfile, path=path) for resultfile in resultfiles]

    return render_template(
        'sandbox.html',
        files=notebooks
    )


def get_extension(filename):
    try:
        extension = filename.rsplit('.', 1)[1].lower()
    except IndexError:
        extension = None

    return extension


@app.route("/flukso/<fluksoid>")
def flukso(fluksoid):
    f = hp.find_device(fluksoid)

    if f is None:
        flash('Your FluksoID was not found in our database.\
        If you want to see OpenGrid analyses for your Flukso, please fill in the form below.')
        return redirect(url_for('development'))

    sensors = f.get_sensors()
    sensors.sort(key=lambda x: x.type)

    return render_template(
        'flukso.html',
        flukso=f,
        sensors=sensors
    )


@app.route("/sensor/<sensorid>", methods=['GET', 'POST'])
def sensor(sensorid):
    s = hp.find_sensor(sensorid)

    if s is None:
        abort(404)

    form = Recalculate()
    if request.method == 'POST' and form.validate():
        try:
            mvreg_sensor.compute(s, pd.Timestamp(form.start.data), pd.Timestamp(form.end.data))
            flash("Succes")
        except Exception as e:
            print(e)
            flash(str(e))
    else:
        flash("Form not validated")

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

    # create multivariable regression plots
    filename = 'multivar_results_{}.png'.format(s.key)
    analyses.append(
        plot.Figure(
            title='Monthly model and predictions',
            content=filename,
            description=u"This plot shows the monthly data and the model for your {sensordescription} <br><br>\
                             Do you think this is useful? Let us know in the\
                             <a href=\"https://groups.google.com/d/forum/opengrid-private\">forum</a>.".format(
                sensordescription=s.description)
        )
    )
    filename = 'multivar_prediction_weekly_{}.png'.format(s.key)
    analyses.append(
        plot.Figure(
            title='Weekly predictions and measurements',
            content=filename,
            description=u"This plot shows the weekly expected value and the measured value for your {sensordescription} <br><br>\
                                 Do you think this is useful? Let us know in the\
                                 <a href=\"https://groups.google.com/d/forum/opengrid-private\">forum</a>.".format(
                sensordescription=s.description)
        )
    )
    filename = 'multivar_model_{}.png'.format(s.key)
    analyses.append(
        plot.Figure(
            title='Monthly model',
            content=filename,
            description=u"This plot shows the monthly data and the model for your {sensordescription} <br><br>\
                                 Do you think this is useful? Let us know in the\
                                 <a href=\"https://groups.google.com/d/forum/opengrid-private\">forum</a>.".format(
                sensordescription=s.description)
        )
    )

    found_analyses = []
    for analysis in analyses:
        if analysis.has_content():
            if type(analysis) == plot.Figure:
                if figure_exists(analysis._content):
                    found_analyses.append(analysis)
            else:
                found_analyses.append(analysis)

    return render_template(
        'sensor.html',
        sensor=s,
        analyses=found_analyses,
        form=form
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


@app.route("/test", methods=['GET', 'POST'])
@app.route("/test/<guid>")
def download_regression(guid=None):
    form = DownloadRegressionForm()
    if request.method == 'POST' and form.validate():
        try:
            mvreg_sensor.compute(form.guid.data, pd.Timestamp(form.start.data), pd.Timestamp(form.end.data))
            flash("Succes")
        except Exception as e:
            print(e)
            flash(str(e))
    else:
        flash("Form not validated")
    if guid is not None:
        form.guid.data = guid

    return render_template(
        'download_regression.html',
        form=form
    )


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
                filepath = safe_join(download_path, filename)
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


@app.route("/slack_callback", methods=['POST'])
def slack():
    payload = request.get_json(force=True)

    message = {
        "attachments": [
                {
                    "fallback": "OpenGrid.be callback",
                    "pretext": "Hello! This is OpenGrid.be speaking. Somebody pressed a button which has generated this message",
                    "text": "```{}```".format(json.dumps(payload, indent=2,
                                                         sort_keys=True)),
                    "mrkdwn_in": ["text"],
                }
            ]
        }
    slackbot.post_json(message)

    return Response(status=200)


@app.route("/admin", methods=['GET', 'POST'])
@login_required
@contributor_required
def admin():
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
        'admin.html',
        form=form
    )
