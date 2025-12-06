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
        db.create_all()

        from .routes.groups import groups_bp

        app.register_blueprint(groups_bp, url_prefix="/groups")

    return app
