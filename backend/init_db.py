# backend/init_db.py
from backend import app, db
from backend.database import db as _db  # if your structure uses backend.database
# If your app creates db in app.py, just import and call create_all
with app.app_context():
    db.create_all()
    print("Database created (errandbuddy.db)")
