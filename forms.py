from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, DateTimeField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo
import datetime


class SignUpForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Confirm Password')
    submit = SubmitField("Sign Up")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class NewListForm(FlaskForm):
    list_name = StringField("List Name", validators=[DataRequired()])
    submit = SubmitField("Submit")


class NewTaskForm(FlaskForm):
    # the date_created and progress fields are automatically created and filled
    task_name = StringField("Task Name", validators=[DataRequired()])
    description = StringField("Task Description")
    deadline = StringField("Deadline - can write in any format (eg. August 18, 2021 at 3:30PM, 08/18/2021, TBD, Soon)",
                           default=datetime.datetime.now().strftime('%B %d, %Y at %I:%M%p'),
                           validators=[DataRequired()])
    # deadline = DateTimeField("Deadline (eg. '2021-08-18,11:40PM' for August 18, 2021 at 11:40 PM)",
    #                          format='%Y-%m-%d,%I:%M%p',
    #                          default=datetime.datetime(month=8, day=18, year=2021, hour=23, minute=40))
    parent_list = SelectField("Choose List to Populate Task With", validators=[DataRequired()])
    submit = SubmitField("Submit")