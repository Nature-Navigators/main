from app import app
from db import db
# create db tables within app context
with app.app_context():
    db.create_all()
