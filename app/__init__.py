import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap

app=Flask(__name__)
app.config.from_object('config')

#file with sender config. for email confirmation 
app.config.from_pyfile('config.cfg')

db=SQLAlchemy(app)

#load Flask-Bootstrap
bootstrap = Bootstrap(app)

#Create LoginManager class from Flask-Login
lm = LoginManager()
lm.init_app(app)
#redirect to login
lm.login_view='signin'

from app import views, models