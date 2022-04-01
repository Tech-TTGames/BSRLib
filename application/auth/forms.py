from flask_wtf import FlaskForm, RecaptchaField
from flask import current_app
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from application.models import User
import re

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    recaptcha = RecaptchaField()
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    mail = StringField('Email', validators=[DataRequired(),Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password_ver = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    recaptcha = RecaptchaField()
    submit = SubmitField('Register')
        
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
                raise ValidationError('Username Taken!')
        user = User.query.filter_by(calibre_usrname=re.sub('[^\w \-]+','',username.data)).first()
        if user is not None:
                raise ValidationError('Username Taken! (when cleaned)')
    
    def validate_mail(self, mail):
        user = User.query.filter_by(email=mail.data).first()
        if user is not None:
            raise ValidationError('Email already in use!')
        domain = mail.data.split('@')[1]
        if domain not in current_app.config['VALID_DOMAINS']:
                raise ValidationError('Illegal email address (domain not on whitelist)')


class AccountRecoveryRequestForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(),Email()])
    recaptcha = RecaptchaField()
    submit = SubmitField('Request Password Reset')

class AccountRecoveryForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password_ver = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    recaptcha = RecaptchaField()
    submit = SubmitField('Set New Password')

class ControlPanel(FlaskForm):
    usertoedit = StringField('Username', validators=[DataRequired()])
    changename = BooleanField('Change username?')
    new_name = StringField('New Username')
    changemail = BooleanField('Change Email?')
    new_email = StringField('New Email')
    make_admin = BooleanField('Toggle Admin?')
    deactivate_account = BooleanField('Toggle Active?')
    lock_account = BooleanField('Toggle Lock?')
    reset_calibre = BooleanField('Reset Calibre?')
    password_confirm = PasswordField('Enter password to Confirm actions', validators=[DataRequired()])
    proceed = SubmitField('Execute')

    def validate_usertoedit(self, usertoedit):
        user = User.query.filter_by(username=usertoedit.data).first()
        if user is None:
            return ValidationError('User not found!')
    
    def validate_new_name(self,new_name):
        if new_name.data is not None:
            user = User.query.filter_by(username=new_name.data).first()
            if user is not None:
                raise ValidationError('Username Taken!')
            user = User.query.filter_by(calibre_usrname=re.sub('[^\w \-]+','',new_name.data)).first()
            if user is not None:
                raise ValidationError('Username Taken! (when cleaned)')

    def validate_new_email(self, new_email):
        if not(new_email.data is None or new_email.data ==''):
            if not re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',new_email.data):
                raise ValidationError('Invalid email adress!')
            user = User.query.filter_by(email=new_email.data).first()
            if user is not None:
                raise ValidationError('Email already in use!')