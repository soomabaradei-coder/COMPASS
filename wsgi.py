"""Production entry point (gunicorn wsgi:app).

Ensures the database exists and is seeded before the app serves requests.
"""
from app import app
from db import init_db

init_db()

if __name__ == "__main__":
    app.run()
