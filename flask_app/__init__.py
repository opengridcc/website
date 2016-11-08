import sys
import os
from flask import Flask
from flask_dance.contrib.github import make_github_blueprint

app = Flask(__name__)
SECRET_KEY = "secret_key"  # TODO add a real key in the config file
app.config.from_object(__name__)

import config

c = config.Config()

try:
    env = c.get('env', 'type')
except:
    env = 'prod'

try:
    from opengrid.library import houseprint
    from opengrid.library import slack
except ImportError:
    sys.path.append(c.get('backend', 'opengrid'))
    from opengrid.library import houseprint
    from opengrid.library import slack

try:
    hp = houseprint.Houseprint()
except:
    print("Connection failed, loading houseprint from cache")
    hp = houseprint.load_houseprint_from_file("cache_hp.hp")
else:
    hp.save("cache_hp.hp")

hp.init_tmpo()

if env == 'prod':
    blueprint = make_github_blueprint(
        client_id=c.get('github', 'clientid'),
        client_secret=c.get('github', 'clientsecret'),
    )
    app.register_blueprint(blueprint, url_prefix="/login")

sandbox_path = os.path.join(os.path.dirname(__file__), "static", "sandbox")
if not os.path.exists(sandbox_path):
    os.mkdir(sandbox_path)
download_path = os.path.join(os.path.dirname(__file__), "static", "downloads")
if not os.path.exists(download_path):
    os.mkdir(download_path)

slack_url = c.get('slack', 'webhook')
slack_username = c.get('slack', 'username')
slack_channel = c.get('slack', 'channel')
slackbot = slack.Slack(url=slack_url, username=slack_username,
                       channel=slack_channel)

from flask_app import views
