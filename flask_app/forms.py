from flask_wtf import Form
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired
from wtforms.fields.html5 import DateField
import datetime as dt


class SearchForm(Form):
    search_string = StringField('search_string', validators=[DataRequired()])


class DownloadForm(Form):
    dt2 = DateField('Pick a Date', format="%m/%d/%Y")
    guid = StringField('sensor_id', validators=[DataRequired()])
    start = DateField('start', format="%d-%m-%Y", default=dt.date(year=2016, month=1, day=1))
    end = DateField('end', format="%d-%m-%Y", default=dt.date.today())
    resample = SelectField('resample', choices=[('min','minutes'), ('h','hours'), ('d', 'days'), ('w', 'week'), ('m', 'month'), ('raw', 'raw')])


class DownloadRegressionForm(Form):
    dt2 = DateField('Pick a Date', format="%m/%d/%Y")
    guid = StringField('sensor_id', validators=[DataRequired()])
    start = DateField('start', format="%m/%d/%Y", default=dt.date(year=2016, month=1, day=1))
    end = DateField('end', format="%m/%d/%Y", default=dt.date.today())
    resample = SelectField('resample',
                           choices=[('min', 'minutes'), ('h', 'hours'), ('d', 'days'), ('w', 'week'), ('m', 'month'),
                                    ('raw', 'raw')])


class EmptyForm(Form):
    pass