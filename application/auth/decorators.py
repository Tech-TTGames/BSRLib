from functools import wraps

from flask import flash,redirect,url_for
from flask_login import current_user, logout_user

def verify_usr(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.confirmed:
            flash('Activate your account before accessing this part of the service!', category='warning')
            return redirect(url_for('auth.inactive'))
        if current_user.lock:
            flash('Your account is locked! Contact the administrator!',category='warning')
            logout_user()
            return redirect(url_for('auth.login'))
        return func(*args, **kwargs)

    return decorated_function