import os
from flask import render_template, flash, redirect, url_for, request, send_from_directory, current_app
from flask.helpers import flash
from werkzeug.utils import redirect
from application.main.forms import ButtonForm, EditProfileForm, PostForm
from application.models import *
from flask_login import current_user, login_required, logout_user
from datetime import datetime
from random import choice
from werkzeug.exceptions import ImATeapot
from application.auth.decorators import verify_usr
from application.main import bp
from re import sub

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@bp.route('/')
@bp.route('/index', methods=['GET','POST'])
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(announcment=True).order_by(Post.timestamp.desc()).paginate(page,current_app.config['POSTS_PER_PAGE'], True)
    stats = (Post.query.count(),User.query.filter_by(confirmed=True,lock=False).count(),User.query.filter(User.calibre_pass != None).count())
    next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None
    if current_user.is_authenticated:
        if not current_user.confirmed:
            flash('Activate your account or log out to check the index!', category='warning')
            return redirect(url_for('auth.inactive'))
        if current_user.lock:
            flash('Your account is locked! Contact the administrator!',category='warning')
            logout_user()
            return redirect(url_for('auth.login'))
        if current_user.admin:
            form = PostForm()
            if form.validate_on_submit():
                post = Post(body=form.post.data, usr_id=current_user.id, announcment=True)
                db.session.add(post)
                db.session.commit()
                flash('Your post is now live!')
                return redirect((url_for('main.index')))
            return render_template("index.html", title='Home Page', posts=posts.items, next_url=next_url, prev_url=prev_url, form=form, stat=stats)
    return render_template('index.html',title="Home Page", posts=posts.items, next_url=next_url, prev_url=prev_url, stat=stats)

@bp.route('/u/<username>')
@login_required
@verify_usr
def user(username):
    form = ButtonForm()
    user = User.query.filter_by(username=username).first_or_404()
    if user.lock:
        flash(category='warning',message='This account was locked!')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], True)
    next_url = url_for('main.user', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) if posts.has_prev else None
    return render_template('user.html',user=user, posts=posts.items, title=f"{username}'s User Page", form=form, next_url=next_url, prev_url=prev_url)

@bp.route('/u/<username>/follow', methods=['POST'])
@login_required
@verify_usr
def follow(username):
    form = ButtonForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(f'User {username} not found!')
            return redirect(url_for('main.index'))
        elif user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('main.index'))
        current_user.follow_ops(user,1)
        db.session.commit()
        flash(f'You are now following {username}!')
        return redirect(url_for('main.user',username=username))
    else:
        return redirect(url_for('main.index'))

@bp.route('/u/<username>/unfollow', methods=['POST'])
@login_required
@verify_usr
def unfollow(username):
    form = ButtonForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(f'User {username} not found!')
            return redirect(url_for('main.index'))
        elif user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('main.index'))
        current_user.follow_ops(user,0)
        db.session.commit()
        flash(f'You have stopped following {username}!')
        return redirect(url_for('main.user',username=username))
    else:
        return redirect(url_for('main.index'))

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
@verify_usr
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        if current_user.username != form.username.data:
            current_user.username = form.username.data
            current_user.calibre_usrname = None
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@bp.route('/lib_access', methods=['GET','POST'])
@login_required
@verify_usr
def calibre_access():
    form = ButtonForm()
    if not current_user.calibre_pass:
        if form.is_submitted():
            chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!#%&*+,./<=>?@\^_{-}~"
            calibre_pass = ''.join(choice(chars) for _ in range(10))
            current_user.calibre_pass = calibre_pass
            os.system(f'calibre-server --userdb "{ current_app.config["CALIBRE_DB_PATH"] }" --manage-users add "{ current_user.calibre_usrname }" "{ calibre_pass }"')
            if not current_user.admin:
                os.system(f'calibre-server --userdb "{ current_app.config["CALIBRE_DB_PATH"] }" --manage-users readonly "{ current_user.calibre_usrname }" set')
            db.session.commit()
            flash(f"Your account was added!")
            return redirect(url_for('main.calibre_access'))
    elif not current_user.calibre_usrname:
        os.system(f'calibre-server --userdb "{ current_app.config["CALIBRE_DB_PATH"] }" --manage-users remove "{ current_user.calibre_usrname }"')
        os.system(f'calibre-server --userdb "{ current_app.config["CALIBRE_DB_PATH"] }" --manage-users remove "{ current_user.username }"')
        current_user.calibre_usrname = sub('[^\w \-]+','',current_user.username)
        current_user.calibre_pass = None
        db.session.commit()
        flash('Account fix in progress... Your password will be changed.', category='error')
        return redirect(url_for('main.calibre_access'))
    return render_template('calibre_access.html',user=current_user, form=form, title='Calibre Library Access')

@bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@bp.route('/forum', methods=['GET','POST'])
@login_required
@verify_usr
def forum():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, usr_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect((url_for('main.forum')))
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page,current_app.config['POSTS_PER_PAGE'], True)
    next_url = url_for('main.forum', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.forum', page=posts.prev_num) if posts.has_prev else None
    return render_template("forum.html", title='Public Forum', posts=posts.items, next_url=next_url, prev_url=prev_url,mode=0,form=form)

@bp.route('/forum/follwed-feed')
@login_required
@verify_usr
def followedfeed():
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(page, current_app.config['POSTS_PER_PAGE'], True)
    next_url = url_for('main.followedfeed', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.followedfeed', page=posts.prev_num) if posts.has_prev else None
    return render_template("forum.html", title='Followed Feed', posts=posts.items, next_url=next_url, prev_url=prev_url,mode=1)

@bp.route('/tea')
@bp.route('/teapot')
def teapot():
    raise ImATeapot