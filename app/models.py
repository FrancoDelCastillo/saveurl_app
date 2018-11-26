from app import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(99),nullable=False)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
    user_emails = db.relationship('Emails')
    user_posts = db.relationship('Posts')

class Emails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50),nullable=False)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
    main_email = db.Column(db.Boolean,nullable=False, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    url_base = db.Column(db.String, nullable=False)
    url_img = db.Column(db.String, nullable=False)
    url_dir = db.Column(db.String,nullable=False)     
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_post = db.Column(db.Integer, db.ForeignKey('users.id'))