from flask import Flask
from .db import db
from .models.group import Group
from .models.group_user import GroupUser
from .models.event import Event
from .models.availability import Availability
from .models.job import Job
from .models.interval import Interval

import os
import redis

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    app.redis_client = redis.from_url(redis_url, decode_responses=True)

    with app.app_context():
        _wait_for_db_and_create_tables()

        from .routes.groups import groups_bp
        from .routes.events import events_bp

        app.register_blueprint(groups_bp, url_prefix="/groups")        
        app.register_blueprint(events_bp, url_prefix="/events")

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