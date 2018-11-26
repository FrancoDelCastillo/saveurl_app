from flask import session
from app import db

db.create_all()
db.session.commit()