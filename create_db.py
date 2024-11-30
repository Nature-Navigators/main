from app import app
from db import db

# Create all database tables within the app context
with app.app_context():
    db.create_all()
