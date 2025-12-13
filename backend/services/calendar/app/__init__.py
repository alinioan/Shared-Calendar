from flask import Flask
from .db import db
from .models.group import Group
from .models.group_user import GroupUser
from .models.event import Event
from .models.availability import Availability

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)

    with app.app_context():
        _wait_for_db_and_create_tables()

        from .routes.groups import groups_bp

        app.register_blueprint(groups_bp, url_prefix="/groups")

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