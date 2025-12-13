from flask import Flask
from .db import db
from .models.user import User

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)

    with app.app_context():
        _wait_for_db_and_create_tables()

        from .routes.profile import profile_bp
        from .routes.sync import sync_bp

        app.register_blueprint(profile_bp, url_prefix="/profile")
        app.register_blueprint(sync_bp, url_prefix="/sync")

    return app


def _wait_for_db_and_create_tables(retries=5, delay=3):
    import time
    from sqlalchemy.exc import OperationalError

    for attempt in range(retries):
        try:
            db.create_all()
            print("Database connected and tables created.")
            return
        except OperationalError as e:
            print(f"Database connection failed (attempt {attempt + 1}/{retries}): {e}")
            time.sleep(delay)

    raise Exception("Could not connect to the database after several attempts.")