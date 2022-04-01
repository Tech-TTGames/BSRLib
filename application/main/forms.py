from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from application.models import User
from flask_login import current_user
from re import sub

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About Me', validators=[Length(min=0,max=140)])
    submit = SubmitField('Submit')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None and user != current_user:
            raise ValidationError('Username Taken!')
        user = User.query.filter_by(calibre_usrname=sub('[^\w \-]+','',username.data)).first()
        if user is not None and user != current_user:
                raise ValidationError('Username Taken! (when cleaned)')


class ButtonForm(FlaskForm):
    initialize = SubmitField('Register!')

class PostForm(FlaskForm):
    post = TextAreaField('Say Something',validators=[DataRequired(),Length(min=3,max=140)])
    submit = SubmitField('Submit')