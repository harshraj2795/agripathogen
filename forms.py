from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional


class SignupForm(FlaskForm):
    name     = StringField('Full Name',  validators=[DataRequired(), Length(min=2, max=100)])
    email    = StringField('Email',      validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm  = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit   = SubmitField('Create Account')


class LoginForm(FlaskForm):
    email       = StringField('Email',    validators=[DataRequired(), Email()])
    password    = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit      = SubmitField('Sign In')


class RequestResetForm(FlaskForm):
    email  = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password',     validators=[DataRequired(), Length(min=6)])
    confirm  = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit   = SubmitField('Reset Password')


class NoteForm(FlaskForm):
    note   = TextAreaField('Note', validators=[Optional(), Length(max=300)],
                           render_kw={'placeholder': 'e.g. Field 3, north section', 'rows': 2})
    submit = SubmitField('Save Note')