from flask_wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired

class SearchForm(Form):
    search_string = StringField('search_string', validators=[DataRequired()])

class DownloadForm(Form):
    sensor_id = StringField('sensor_id', validators=[DataRequired()])