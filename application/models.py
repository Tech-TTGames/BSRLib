import argon2
from application import db, login
from datetime import datetime
from argon2 import PasswordHasher as ph
from flask_login import UserMixin
from flask import current_app
from hashlib import md5
from itsdangerous import URLSafeTimedSerializer

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow())
    calibre_pass = db.Column(db.String(128))
    calibre_usrname = db.Column(db.String(128), unique=True)
    confirmed = db.Column(db.Boolean, default=False)
    admin = db.Column(db.Boolean, default=False)
    lock = db.Column(db.Boolean, default=False)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'
    
    def avatar(self,size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'
    
    def set_Password(self, password):
        self.password_hash = ph().hash(password)
    
    def verify_Password(self, password):
        passhash = self.password_hash
        try:
            ph().verify(passhash, password)
            if ph().check_needs_rehash(passhash):
                self.set_Password(password)
            return True
        except argon2.exceptions.VerifyMismatchError:
            return False
    
    def is_following(self,user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0
    
    def follow_ops(self,user,op):
        if op:
            if not self.is_following(user):
                self.followed.append(user)
        else:
            if self.is_following(user):
                self.followed.remove(user)
    
    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.usr_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(usr_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())
    
    def get_token(self):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        data = int(self.id)
        return serializer.dumps(obj=data, salt=current_app.config['SECURITY_SALT'])
    
    @staticmethod
    def verify_token(token,expiration=600):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            id = serializer.loads(token,salt=current_app.config['SECURITY_SALT'],max_age=expiration)
        except:
            return
        return User.query.get(int(id))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    usr_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    announcment = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Post {self.body}>'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))