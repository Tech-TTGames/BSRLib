from flask import render_template, current_app
from application.sendmail import send_email

def send_recovery(user):
    token = user.get_token()
    send_email('[BSRLib] Account Recovery',sender=current_app.config['ADMINS'][0],recipients=[user.email]
    ,text_body=render_template('email/recover.txt',user=user,token=token),html_body=render_template('email/recover.html',user=user,token=token))

def send_activate(user):
    token = user.get_token()
    send_email('[BSRLib] Account Activation',sender=current_app.config['ADMINS'][0],recipients=[user.email]
    ,text_body=render_template('email/activate.txt',user=user,token=token),html_body=render_template('email/activate.html',user=user,token=token))