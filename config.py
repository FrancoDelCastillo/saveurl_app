import os

WTF_CSRF_ENABLED = True
SECRET_KEY = 'top-secret-top'

basedir = os.path.abspath(os.path.dirname(__file__))

#pointing to Heroku Postgres DB or to local directory
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')

#turn off the Flask-SQLAlchemy event system
SQLALCHEMY_TRACK_MODIFICATIONS = False

