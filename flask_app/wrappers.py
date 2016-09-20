from flask_dance.contrib.github import github
from functools import wraps
from flask import abort, flash, session, g

from flask_app import env, app


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not user_is_authenticated():
            abort(401)
        return f(*args, **kwargs)
    return decorated_function


def contributor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not user_is_contributor():
            flash('You need to be a contributor to the OpenGrid project to view this page!')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def user_is_authenticated():
    if env == 'dev':
        return True
    return github.authorized and 'username' in session


def user_is_contributor():
    if env == 'dev':
        return True
    return 'contributor' in session and session['contributor'] is True


@app.before_request
def before_request():
    g.user_is_authenticated = user_is_authenticated()
    g.user_is_contributor = user_is_contributor()
