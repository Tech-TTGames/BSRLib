from flask import render_template, redirect, url_for, flash, request, current_app
from werkzeug.urls import url_parse
from werkzeug.exceptions import NotFound, Forbidden
from flask_login import login_user, logout_user, current_user, login_required
from application import db
from application.auth import bp
from application.auth.forms import RegistrationForm, AccountRecoveryForm, AccountRecoveryRequestForm, LoginForm, ControlPanel
from application.models import User
from application.auth.sendmail import send_activate, send_recovery
from re import sub
from os import system

@bp.route('/inactive')
@login_required
def inactive():
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    flash('Please confirm your account!')
    return render_template('/auth/inactive.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.verify_Password(form.password.data):
            flash('Invalid Username or Password!', category='warning')
            return redirect(url_for('auth.login'))
        if user.lock:
            flash('Your account is locked! Contact the administrator!', category='warning')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('/auth/login.html', title='Sing In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,email=form.mail.data,calibre_usrname=sub('[^\w \-]+','',form.username.data))
        user.set_Password(form.password.data)
        db.session.add(user)
        db.session.commit()
        user = User.query.filter_by(username=form.username.data).first()
        send_activate(user)
        flash(f"Thank you for registering {form.username.data}! Please check your email for an activation link.")
        return redirect(url_for('auth.login'))
    return render_template('/auth/register.html', title='Register', form=form)

@bp.route('/activate')
@login_required
def activate():
    token = request.args.get('t')
    user = User.verify_token(token)
    if user is None:
        raise NotFound
    if user.confirmed:
        flash('Account already active!')
    elif user != current_user:
        flash('Activation link for another account!', category='warning')
    else:
        user.confirmed = True
        db.session.add(user)
        db.session.commit()
        flash('Account activated!')
    return redirect(url_for('main.index'))

@bp.route('/resend')
@login_required
def resend():
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    send_activate(current_user)
    flash('A new activation link was sent!')
    return redirect(url_for('auth.inactive'))

@bp.route('/request_recovery',methods=['GET','POST'])
def recover_account_request():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    form = AccountRecoveryRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_recovery(user)
        flash('Check your email for recovery instructions!')
        return redirect(url_for('auth.login'))
    return render_template('/auth/account_recovery_request.html',title='Recover Account', form=form)

@bp.route('/recover',methods=['GET','POST'])
def recover():
    token = request.args.get('t')
    user = User.verify_token(token)
    if user is None:
        raise NotFound
    if not user:
        return redirect(url_for('main.index'))
    form = AccountRecoveryForm()
    if form.validate_on_submit():
        user.set_Password(form.password.data)
        db.session.commit()
        flash('New Password successfully set!')
        return redirect(url_for('auth.login'))
    return render_template('/auth/account_recovery.html',form=form, title='Set New Password')

@bp.route('/control',methods=['GET','POST'])
@login_required
def control_panel():
    if not current_user.admin:
        raise Forbidden
    else:
        form = ControlPanel()
        if form.validate_on_submit():
            if not current_user.verify_Password(form.password_confirm.data):
                flash('Invalid Password!', category='warning')
                return redirect(url_for('auth.control_panel'))
            user = User.query.filter_by(username=form.usertoedit.data).first()
            actions_run = "Executed:"
            if form.changename.data:
                user.username = form.new_name.data
                user.calibre_usrname = sub('[^\w \-]+','',form.username.data)
                actions_run += f' Name changed to {form.new_name.data};'
            if form.changemail.data:
                user.email = form.new_email.data
                actions_run += f' Email changed to {form.new_email.data};'
            if form.make_admin.data:
                user.admin = not user.admin
                actions_run += f'Toggled admin to {user.admin};'
            if form.deactivate_account.data:
                user.confirmed = not user.confirmed
                actions_run += f'Toggled active to {user.confirmed}'
            if form.lock_account.data:
                user.lock = not user.lock
                actions_run += f'Toggled lock to {user.lock}'
            if form.reset_calibre.data:
                system(f'calibre-server --userdb "{ current_app.config["CALIBRE_DB_PATH"] }" --manage-users remove "{ current_user.calibre_usrname }"')
                user.calibre_pass = None
                actions_run += 'Calibre Data Reset;'
            actions_run += f' for {user.username}!'
            db.session.commit()
            flash(actions_run)
            return redirect(url_for('auth.control_panel'))
        return render_template('/auth/control_panel.html',form=form, title='ACP')