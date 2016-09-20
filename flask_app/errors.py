from flask import flash, redirect, url_for

from flask_app import app


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
